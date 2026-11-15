"""Drought-risk model — OWNED BY THE `ml` AGENT.

Interface (DO NOT change the signature — the pipeline + `main` depend on it):

    predict_risk(features: dict) -> dict

Input `features` (all optional; missing keys default sanely):
    rainfall_anomaly   float  # (recent - normal) / normal; negative = drier
    soil_moisture      float  # m3/m3, ~0.05..0.45
    ndvi_trend         float  # slope; negative = vegetation declining
    et                 float  # evapotranspiration, mm/day
    temp_anomaly       float  # deg C vs climatology
    solar_radiation    float  # MJ/m2/day

Output:
    {
      "risk_score": int,       # 0..100
      "risk_level": "low" | "moderate" | "high",
      "confidence": float,     # 0..1
      "drivers": [str, ...],   # human-readable top factors
    }

HOW IT WORKS
  The trained bundle (app/ml/risk_model.joblib, built by app.ml.train) carries a
  StandardScaler, an IsolationForest, a RandomForest + LogisticRegression (for
  the backtest), and the climate calibration (mu/sd).

  * risk_score — a DIRECTIONAL signed z-score composite (see scoring.py): drier
    always raises the score, which keeps the score monotonic and explainable.
  * multivariate_anomaly — the IsolationForest's view of how UNUSUAL the overall
    combination is (symmetric), feeding confidence and an "unusual combination"
    note rather than the score itself.
  * confidence — rises when the indicators agree and the signal is decisive.
  * drivers — the top features pushing risk up, with their z-score magnitude.

  No network, no training at call time: the bundle is loaded once at import. If
  it is missing, `predict_risk` falls back to a transparent linear estimate so
  the app still runs (confidence pinned low to advertise that).
"""
from __future__ import annotations

import numpy as np

from .features import FEATURE_ORDER, feature_vector
from . import scoring as S
from . import store as ST

# Load the trained bundle once. Never crash import if it is missing/corrupt.
try:
    MODEL = ST.load_bundle()
except Exception:  # pragma: no cover - defensive
    MODEL = None


def _level(score: int) -> str:
    if score < 40:
        return "low"
    if score < 70:
        return "moderate"
    return "high"


# --------------------------------------------------------------------------- #
# IsolationForest multivariate anomaly (unsupervised backbone)
# --------------------------------------------------------------------------- #
def multivariate_anomaly(features: dict) -> float:
    """How unusual is this combination of conditions, in [0, 1]?

    1.0 = more anomalous than every training season; 0.0 = right in the normal
    cluster. Computed from the IsolationForest decision function, ranked against
    the training distribution. Symmetric by design (a freak-wet season is
    anomalous too), which is why it informs confidence, not the risk score.
    """
    if MODEL is None:
        return 0.0
    scaled = MODEL["scaler"].transform(feature_vector(features).reshape(1, -1))
    decision = float(MODEL["iforest"].decision_function(scaled)[0])
    sorted_train = MODEL["if_decision_sorted"]
    n = len(sorted_train)
    # fraction of training seasons at least as "normal" as this point
    above = n - int(np.searchsorted(sorted_train, decision, side="left"))
    return float(np.clip(above / n, 0.0, 1.0))


# --------------------------------------------------------------------------- #
# Human-readable drivers
# --------------------------------------------------------------------------- #
def _driver_phrase(feature: str, z: float) -> str:
    mag = abs(z)
    phrases = {
        "rainfall_anomaly": f"rainfall {mag:.1f}σ below normal",
        "soil_moisture": f"soil moisture {mag:.1f}σ below normal",
        "ndvi_trend": f"vegetation declining (NDVI {mag:.1f}σ below normal)",
        "et": f"high crop water demand (ET {mag:.1f}σ above normal)",
        "temp_anomaly": f"temperatures {mag:.1f}σ above normal",
        "solar_radiation": f"strong solar radiation ({mag:.1f}σ above normal)",
    }
    return phrases[feature]


def _drivers(scaled: np.ndarray, contrib: np.ndarray, anomaly: float, index: float) -> list:
    order = np.argsort(contrib)[::-1]  # biggest upward push on risk first
    drivers = [
        _driver_phrase(FEATURE_ORDER[i], scaled[i])
        for i in order
        if contrib[i] > 0.03
    ][:3]
    if not drivers:
        return ["conditions near or better than seasonal normal"]
    if anomaly >= 0.85 and index > 0:
        drivers.append("unusual combination of conditions for this location")
    return drivers


# --------------------------------------------------------------------------- #
# Main entry point
# --------------------------------------------------------------------------- #
def predict_risk(features: dict) -> dict:
    if MODEL is None:
        return _fallback_predict(features)

    scaled = MODEL["scaler"].transform(feature_vector(features).reshape(1, -1))[0]
    contrib = S.contributions(scaled)
    index = float(contrib.sum())
    score = S.index_to_score(index, MODEL["mu"], MODEL["sd"])

    anomaly = multivariate_anomaly(features)

    # confidence: agreement among indicators + decisiveness of the signal,
    # nudged up when an anomalous combination corroborates a dry verdict
    abs_total = float(np.abs(contrib).sum())
    if abs_total > 1e-9:
        agree = float(np.abs(contrib[np.sign(contrib) == np.sign(index)]).sum()) / abs_total
    else:
        agree = 0.0
    sd = MODEL["sd"] if MODEL["sd"] > 1e-9 else 1.0
    decisiveness = min(1.0, abs(index - MODEL["mu"]) / sd / 1.5)
    anomaly_if_dry = anomaly if index > 0 else 0.0
    confidence = float(
        np.clip(0.42 + 0.33 * agree + 0.15 * decisiveness + 0.10 * anomaly_if_dry, 0.3, 0.97)
    )

    return {
        "risk_score": int(score),
        "risk_level": _level(score),
        "confidence": round(confidence, 2),
        "drivers": _drivers(scaled, contrib, anomaly, index),
    }


# --------------------------------------------------------------------------- #
# Fallback (used only if the trained bundle is unavailable)
# --------------------------------------------------------------------------- #
def _fallback_predict(features: dict) -> dict:
    """Transparent linear estimate. Not the real model — keeps the app green."""
    rainfall_anomaly = float(features.get("rainfall_anomaly", 0.0))
    soil_moisture = float(features.get("soil_moisture", 0.25))
    ndvi_trend = float(features.get("ndvi_trend", 0.0))
    et = float(features.get("et", 4.5))

    score = 50.0
    score += -rainfall_anomaly * 60.0
    score += (0.25 - soil_moisture) * 120.0
    score += -ndvi_trend * 150.0
    score += (et - 4.5) * 5.0
    score = int(max(0, min(100, round(score))))

    drivers = []
    if rainfall_anomaly < -0.10:
        drivers.append("rainfall below normal")
    if soil_moisture < 0.20:
        drivers.append("low soil moisture")
    if ndvi_trend < -0.05:
        drivers.append("declining vegetation (NDVI)")
    if et > 5.0:
        drivers.append("high evapotranspiration")

    return {
        "risk_score": score,
        "risk_level": _level(score),
        "confidence": 0.3,  # low on purpose: fallback, not the trained model
        "drivers": drivers or ["conditions near seasonal normal"],
    }


# Convenience re-export so callers can do `from app.ml.risk import backtest`
# without importing the training/network module eagerly.
def backtest(*args, **kwargs):
    """Run the held-out backtest (see app.ml.train.backtest)."""
    from .train import backtest as _bt

    return _bt(*args, **kwargs)
