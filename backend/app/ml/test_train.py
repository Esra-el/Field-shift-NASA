"""Tests for the training pipeline's offline, network-free pieces.

We fit on a SYNTHETIC per-season table so these stay fast and deterministic.
The real NASA-POWER fetch + fit is exercised by running `train.main()`, not here.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from app.ml import train as T
from app.ml import store as ST
from app.ml.features import FEATURE_ORDER


def _synthetic_table():
    """3 locations x 12 years. Rainfall drives the other features so the
    supervised models have a real signal to learn."""
    rng = np.random.default_rng(0)
    rows = []
    for loc in ["GT", "NI", "HN"]:
        clim = 900.0
        for year in range(2008, 2020):
            # known El Nino years are dry; everything else noisy around normal
            dry = year in (2009, 2015, 2018)
            rain = clim * (0.55 if dry else rng.uniform(0.85, 1.2))
            anom = (rain - clim) / clim
            rows.append(
                {
                    "location": loc,
                    "year": year,
                    "seasonal_rainfall_mm": rain,
                    "rainfall_anomaly": anom,
                    "soil_moisture": float(np.clip(0.25 + anom * 0.3, 0.05, 0.45)),
                    "ndvi_trend": 0.2 * np.tanh(anom * 2),
                    "et": 4.5 - anom * 1.0,
                    "temp_anomaly": -anom * 1.5,
                    "solar_radiation": 20.0 - anom * 2.0,
                }
            )
    return pd.DataFrame(rows)


def _synth_site_payloads():
    import datetime as dt
    import numpy as np

    years = list(range(2010, 2024))
    rng = np.random.default_rng(2)
    params = {k: {} for k in ("PRECTOTCORR", "T2M", "T2M_MAX", "T2M_MIN", "ALLSKY_SFC_SW_DWN", "GWETROOT")}
    for y in years:
        # per-YEAR values so seasonal means carry real inter-annual variance
        rain = 600 + rng.normal(0, 70)
        gwet = 0.40 + rng.normal(0, 0.03)
        tmean_y = 24.0 + rng.normal(0, 0.7)
        solar_y = 20.0 + rng.normal(0, 0.8)
        days = [dt.date(y, m, dd) for m in range(5, 11) for dd in range(1, 29)]
        for d in days:
            k = d.strftime("%Y%m%d")
            params["PRECTOTCORR"][k] = max(0.0, rain) / len(days)
            params["T2M"][k] = tmean_y
            params["T2M_MAX"][k] = tmean_y + 6.0
            params["T2M_MIN"][k] = tmean_y - 6.0
            params["ALLSKY_SFC_SW_DWN"][k] = solar_y
            params["GWETROOT"][k] = gwet
    power = {"properties": {"parameter": params}, "geometry": {"coordinates": [0, 0, 0]}}
    modis = {"subset": [{"calendar_date": f"{y}-06-10", "data": [int((0.5 + rng.normal(0, 0.04)) / 0.0001)]} for y in years], "scale": 0.0001}
    return power, modis


def test_global_sites_span_climates():
    from app.ml import data as D

    assert len(D.GLOBAL_SITES) >= 10
    lats = [s["latitude"] for s in D.GLOBAL_SITES]
    assert any(35 <= lat <= 50 for lat in lats)   # a Mediterranean / temperate point
    assert any(lat < 0 for lat in lats)           # a Southern-hemisphere point


def test_build_global_training_table_is_zscored(monkeypatch):
    from app.ml import data as D

    power, _modis = _synth_site_payloads()
    monkeypatch.setattr(D, "fetch_power", lambda *a, **k: power)
    table = T.build_global_training_table(sites=D.GLOBAL_SITES[:3])
    for col in FEATURE_ORDER + ["year", "location", "seasonal_rainfall_mm"]:
        assert col in table.columns
    # POWER-derived columns are per-site z-scored -> ~0 mean, ~unit spread
    import numpy as np

    for col in ["soil_moisture", "temp_anomaly", "solar_radiation"]:
        assert abs(table[col].mean()) < 0.2
        assert abs(np.std(table[col]) - 1.0) < 0.3
    # NDVI trains neutral (real only at inference)
    assert (table["ndvi_trend"] == 0).all()


def test_proxy_labels_flag_driest_and_known_drought_years():
    table = _synthetic_table()
    y = T.proxy_labels(table)
    assert set(np.unique(y)) <= {0, 1}
    # every known drought year is labelled drought
    for _, r in table.iterrows():
        if r["year"] in T.KNOWN_DROUGHT_YEARS:
            assert y[r.name] == 1
    # a clearly wet year is not
    wettest = table["rainfall_anomaly"].idxmax()
    assert y[wettest] == 0


def test_train_from_table_builds_a_complete_bundle():
    bundle = T.train_from_table(_synthetic_table())
    for key in [
        "feature_order",
        "scaler",
        "iforest",
        "random_forest",
        "logistic_regression",
        "naive_bayes",
        "mu",
        "sd",
        "if_decision_sorted",
        "training_table",
        "proxy_label_note",
        "known_drought_years",
    ]:
        assert key in bundle, f"missing {key}"
    assert bundle["feature_order"] == FEATURE_ORDER
    # models are fitted and callable
    Xs = bundle["scaler"].transform(_synthetic_table()[FEATURE_ORDER].to_numpy())
    assert bundle["random_forest"].predict(Xs).shape[0] == len(_synthetic_table())


def test_cross_validate_reports_recall_first_recommendation():
    cv = T.cross_validate(T.train_from_table(_synthetic_table()))
    assert cv["method"] == "leave-one-year-out"
    # every supervised model reports all three rates, in range
    assert {"logistic_regression", "random_forest", "naive_bayes"} <= set(cv["models"])
    for stats in cv["models"].values():
        for k in ("precision", "recall", "f1"):
            assert 0.0 <= stats[k] <= 1.0
    # the recommendation encodes our aim: pick the highest-recall model
    best_recall = max(m["recall"] for m in cv["models"].values())
    assert cv["models"][cv["recommended"]]["recall"] == best_recall
    assert "recall" in cv["aim"].lower()


def test_bundle_round_trips_through_store(tmp_path):
    bundle = T.train_from_table(_synthetic_table())
    path = tmp_path / "risk_model.joblib"
    ST.save_bundle(bundle, path)
    loaded = ST.load_bundle(path)
    assert loaded is not None
    assert loaded["feature_order"] == FEATURE_ORDER
    assert ST.load_bundle(tmp_path / "does_not_exist.joblib") is None
