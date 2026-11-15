"""Standardized Precipitation Index (SPI) — OWNED BY THE `ml` AGENT.

SPI is the WMO-standard drought measure: how unusual a location's accumulated
precipitation is versus its own history, expressed as a standard-normal value
(negative = drier than normal, 0 = normal). Being per-location and unitless, it
works identically anywhere on Earth — which is how Field Shift goes global.

Method (McKee et al. 1993): fit a gamma distribution to the historical window
totals, convert the latest total's cumulative probability to a z-score via the
inverse normal. Precipitation has a point mass at zero, so we mix in the
empirical zero probability. Short histories fall back to a normal-approx z.
"""
from __future__ import annotations

from typing import List, Sequence

import numpy as np
from scipy.stats import gamma, norm

_MIN_FIT = 8          # need a reasonable sample before trusting a gamma fit
_CLIP = 1e-3          # keep the inverse-normal finite at the tails


def accumulate(monthly: Sequence[float], window: int) -> List[float]:
    """Rolling `window`-month precipitation totals from a monthly series."""
    m = list(monthly)
    return [float(sum(m[i : i + window])) for i in range(len(m) - window + 1)]


def _normal_approx(totals: np.ndarray) -> float:
    std = totals.std()
    if std < 1e-9:
        return 0.0
    return float((totals[-1] - totals.mean()) / std)


def spi_series(window_totals: Sequence[float]) -> np.ndarray:
    """SPI for EVERY element: fit the gamma once, score each window total."""
    totals = np.asarray(list(window_totals), dtype=float)
    n = totals.size
    if n == 0:
        return np.array([])

    positive = totals[totals > 0]
    if n < _MIN_FIT or positive.size < _MIN_FIT:
        std = totals.std()
        return (totals - totals.mean()) / std if std > 1e-9 else np.zeros(n)

    q = float((totals <= 0).sum()) / n
    try:
        a, _loc, scale = gamma.fit(positive, floc=0)
        g = np.where(totals > 0, gamma.cdf(totals, a, loc=0, scale=scale), 0.0)
        cdf = q + (1.0 - q) * g
    except Exception:
        std = totals.std()
        return (totals - totals.mean()) / std if std > 1e-9 else np.zeros(n)

    cdf = np.clip(cdf, _CLIP, 1.0 - _CLIP)
    return norm.ppf(cdf)


def spi_latest(window_totals: Sequence[float]) -> float:
    """SPI of the LAST element given the history of same-window totals."""
    totals = list(window_totals)
    if len(totals) == 0:
        return 0.0
    return float(spi_series(totals)[-1])
