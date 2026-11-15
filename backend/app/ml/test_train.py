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
