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


NORMAL = {
    "rainfall_anomaly": 0.0,
    "soil_moisture": 0.25,
    "ndvi_trend": 0.0,
    "et": 4.5,
    "temp_anomaly": 0.0,
    "solar_radiation": 20.0,
}

STRONG_DROUGHT = {
    "rainfall_anomaly": -0.45,
    "soil_moisture": 0.10,
    "ndvi_trend": -0.15,
    "et": 6.2,
    "temp_anomaly": 1.8,
    "solar_radiation": 24.0,
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
        "rainfall_anomaly": -0.5,   # less rain
        "soil_moisture": 0.08,      # drier soil
        "ndvi_trend": -0.2,         # browning vegetation
        "et": 6.5,                  # higher water demand
        "temp_anomaly": 2.5,        # hotter
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
        "rainfall_anomaly": -0.9,
        "soil_moisture": 0.02,
        "ndvi_trend": -0.25,
        "et": 9.0,
        "temp_anomaly": 5.0,
        "solar_radiation": 30.0,
    }
    assert risk.multivariate_anomaly(weird) > risk.multivariate_anomaly(NORMAL)
    assert risk.multivariate_anomaly(weird) >= 0.8
    assert 0.0 <= risk.multivariate_anomaly(NORMAL) <= 1.0
