"""Directional drought scoring — shared pure math, OWNED BY THE `ml` AGENT.

Both train.py (to calibrate) and risk.py (to answer a request) use this, so it
lives on its own with no heavy deps.

Why a signed z-score composite rather than the IsolationForest for the score:
the IsolationForest is *symmetric* — it flags an unusually WET season as
anomalous too. A drought score must be *directional* (drier is always worse),
which a fixed-sign weighted sum of standardized indicators guarantees. The
IsolationForest's multivariate anomaly feeds confidence instead (see risk.py).
"""
from __future__ import annotations

import numpy as np

from .features import FEATURE_ORDER

# Sign of each feature's contribution to drought risk, aligned to FEATURE_ORDER:
#   rainfall_anomaly, soil_moisture, ndvi_trend  -> less = more risk  (-1)
#   et, temp_anomaly, solar_radiation            -> more = more risk  (+1)
SIGNS = np.array([-1.0, -1.0, -1.0, +1.0, +1.0, +1.0])

# Relative importance. Rainfall dominates rain-fed drought; solar is a minor
# evaporative-demand nudge. Kept as a normalized weighting (sums to 1).
WEIGHTS = np.array([0.30, 0.22, 0.18, 0.14, 0.10, 0.06])

# Logistic shaping of the standardized composite into 0..100.
#   score = 100 * sigmoid(A_SLOPE * z_index + C_OFFSET)
# C_OFFSET = ln(0.35/0.65): a season at the historical-mean composite -> ~35/100
# (most seasons are not droughts, so normal reads LOW), rising smoothly toward
# 100 as conditions dry out.
A_SLOPE = 1.1
C_OFFSET = -0.619


def contributions(scaled: np.ndarray) -> np.ndarray:
    """Per-feature push on risk (positive = raises risk), on standardized inputs."""
    return WEIGHTS * SIGNS * np.asarray(scaled, dtype=float)


def drought_index(scaled: np.ndarray) -> float:
    """Single directional severity number from the standardized feature vector."""
    return float(contributions(scaled).sum())


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + np.exp(-x))


def index_to_score(index: float, mu: float, sd: float) -> int:
    """Map a drought index to an integer 0..100 risk score.

    `mu`/`sd` are the mean/std of the index over the training seasons, so the
    shaping is calibrated to each deployment's own climate, not a magic range.
    """
    sd = sd if sd > 1e-9 else 1.0
    z = (index - mu) / sd
    return int(round(100.0 * _sigmoid(A_SLOPE * z + C_OFFSET)))
