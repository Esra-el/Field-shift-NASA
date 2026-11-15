"""Tests for predict_risk — the live inference entry point.

Two kinds of test here:
  * INVARIANTS the output must always satisfy (shape, ranges, monotonicity) —
    these guard the contract for both the trained model and the fallback.
  * MODEL-BACKED behaviour the transparent fallback cannot produce (a loaded
    model, trained-model confidence, quantified drivers) — these are what drove
    the real implementation.
"""
from __future__ import annotations

from app.ml import risk


# Features are z-scores vs local normal (0 = exactly normal for that place).
NORMAL = {name: 0.0 for name in ["rainfall_anomaly", "soil_moisture", "ndvi_trend", "et", "temp_anomaly", "solar_radiation"]}

STRONG_DROUGHT = {
    "rainfall_anomaly": -2.0,   # 2σ drier than normal
    "soil_moisture": -1.8,
    "ndvi_trend": -1.5,
    "et": 1.5,                  # higher water demand than normal
    "temp_anomaly": 1.8,
    "solar_radiation": 1.0,
}


# --------------------------------------------------------------------------- #
# Invariants (must hold for any implementation)
# --------------------------------------------------------------------------- #
def test_output_shape_and_ranges():
    out = risk.predict_risk(NORMAL)
    assert set(out) == {"risk_score", "risk_level", "confidence", "drivers"}
    assert isinstance(out["risk_score"], int) and 0 <= out["risk_score"] <= 100
    assert out["risk_level"] in {"low", "moderate", "high"}
    assert isinstance(out["confidence"], float) and 0.0 <= out["confidence"] <= 1.0
    assert isinstance(out["drivers"], list) and all(isinstance(d, str) for d in out["drivers"])
    assert out["drivers"]  # never empty


def test_empty_features_defaults_do_not_crash():
    out = risk.predict_risk({})
    assert 0 <= out["risk_score"] <= 100


def test_climatological_normal_season_reads_low_and_calm():
    # a season sitting exactly at the trained climatology is NOT a drought:
    # it must read low with no invented drivers
    means = dict(zip(risk.MODEL["feature_order"], risk.MODEL["scaler"].mean_))
    out = risk.predict_risk(means)
    assert out["risk_level"] == "low"
    assert out["risk_score"] <= 40
    assert out["drivers"] == ["conditions near or better than seasonal normal"]


def test_empty_features_are_calm_not_elevated():
    # neutral defaults must land near climatology, not invent a drought
    out = risk.predict_risk({})
    assert out["risk_level"] == "low"
    assert out["drivers"] == ["conditions near or better than seasonal normal"]


def test_drier_raises_score_monotonically_per_feature():
    base_score = risk.predict_risk(NORMAL)["risk_score"]
    drier_variants = {
        "rainfall_anomaly": -2.0,   # drier than normal
        "soil_moisture": -2.0,      # drier soil than normal
        "ndvi_trend": -2.0,         # browner than normal
        "et": 2.0,                  # higher water demand than normal
        "temp_anomaly": 2.0,        # hotter than normal
    }
    for key, drier_value in drier_variants.items():
        f = dict(NORMAL)
        f[key] = drier_value
        assert risk.predict_risk(f)["risk_score"] >= base_score, f"{key} should not lower risk"


def test_strong_drought_scores_higher_than_normal():
    assert risk.predict_risk(STRONG_DROUGHT)["risk_score"] > risk.predict_risk(NORMAL)["risk_score"]


# --------------------------------------------------------------------------- #
# Model-backed behaviour (fails against the transparent fallback)
# --------------------------------------------------------------------------- #
def test_trained_model_is_loaded():
    assert risk.MODEL is not None, "expected the trained joblib bundle to load"


def test_trained_confidence_beats_the_fallback_on_a_clear_signal():
    # the fallback always returns 0.3; a trained model on an internally
    # consistent strong-drought signal must be clearly more confident
    assert risk.predict_risk(STRONG_DROUGHT)["confidence"] >= 0.6


def test_drivers_are_quantified_for_a_strong_shortfall():
    drivers = risk.predict_risk(STRONG_DROUGHT)["drivers"]
    joined = " ".join(drivers).lower()
    assert "σ" in " ".join(drivers) or "sigma" in joined  # z-scored magnitude, not a vague phrase
    assert any("rain" in d.lower() for d in drivers)


# --------------------------------------------------------------------------- #
# IsolationForest multivariate anomaly backbone
# --------------------------------------------------------------------------- #
def test_isolation_forest_flags_an_obvious_anomaly():
    # a wildly out-of-distribution combination should score far more anomalous
    weird = {
        "rainfall_anomaly": -3.5,
        "soil_moisture": -3.5,
        "ndvi_trend": -3.0,
        "et": 3.5,
        "temp_anomaly": 4.0,
        "solar_radiation": 3.0,
    }
    assert risk.multivariate_anomaly(weird) > risk.multivariate_anomaly(NORMAL)
    assert risk.multivariate_anomaly(weird) >= 0.8
    assert 0.0 <= risk.multivariate_anomaly(NORMAL) <= 1.0


# --------------------------------------------------------------------------- #
# Task 7: z-score representation + global sanity (the Florence bug is gone)
# --------------------------------------------------------------------------- #
def test_feature_defaults_are_neutral_zero():
    from app.ml.features import FEATURE_DEFAULTS

    assert all(v == 0.0 for v in FEATURE_DEFAULTS.values())
    out = risk.predict_risk({})
    assert out["risk_level"] == "low"
    assert out["drivers"] == ["conditions near or better than seasonal normal"]


def _synth_power_latest(wet: bool):
    import datetime as dt

    years = list(range(2012, 2026))
    rng = __import__("numpy").random.default_rng(3)
    params = {k: {} for k in ("PRECTOTCORR", "T2M", "T2M_MAX", "T2M_MIN", "ALLSKY_SFC_SW_DWN", "GWETROOT")}
    for y in years:
        rain = 600 + rng.normal(0, 60)
        gwet = 0.40 + rng.normal(0, 0.03)
        if y == 2025:  # latest season
            rain, gwet = (900.0, 0.55) if wet else (230.0, 0.18)
        days = [dt.date(y, m, dd) for m in range(5, 11) for dd in range(1, 29)]
        for d in days:
            k = d.strftime("%Y%m%d")
            params["PRECTOTCORR"][k] = max(0.0, rain) / len(days)
            params["T2M"][k] = 24.0 + rng.normal(0, 0.5)
            params["T2M_MAX"][k] = 30.0
            params["T2M_MIN"][k] = 18.0
            params["ALLSKY_SFC_SW_DWN"][k] = 20.0
            params["GWETROOT"][k] = gwet
    return {"properties": {"parameter": params}, "geometry": {"coordinates": [11.26, 43.77, 0]}}


def test_florence_wet_latest_season_reads_low(monkeypatch):
    # the Florence bug: a wet recent season must NOT read as drought
    from app.ml import assess as A
    from app.ml import data as D

    monkeypatch.setattr(D, "fetch_power", lambda *a, **k: _synth_power_latest(wet=True))
    monkeypatch.setattr(D, "fetch_modis_ndvi", lambda *a, **k: {"subset": [], "scale": 0.0001})
    feats = A.assess_location(43.77, 11.26)
    out = risk.predict_risk(feats)
    assert out["risk_level"] in {"low", "moderate"}
    assert out["risk_level"] != "high"


def test_global_dry_latest_season_reads_high(monkeypatch):
    from app.ml import assess as A
    from app.ml import data as D

    monkeypatch.setattr(D, "fetch_power", lambda *a, **k: _synth_power_latest(wet=False))
    monkeypatch.setattr(D, "fetch_modis_ndvi", lambda *a, **k: {"subset": [], "scale": 0.0001})
    feats = A.assess_location(43.77, 11.26)
    out = risk.predict_risk(feats)
    assert out["risk_score"] > risk.predict_risk(NORMAL)["risk_score"]
    assert out["risk_level"] in {"moderate", "high"}
