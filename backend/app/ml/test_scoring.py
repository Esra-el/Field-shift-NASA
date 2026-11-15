"""Tests for the shared, pure scoring math (used by both train and inference)."""
from __future__ import annotations

import numpy as np

from app.ml import scoring as S
from app.ml.features import FEATURE_ORDER


def test_signs_and_weights_align_with_feature_order():
    assert len(S.SIGNS) == len(FEATURE_ORDER)
    assert len(S.WEIGHTS) == len(FEATURE_ORDER)
    # drought-direction signs: less rain/soil/ndvi, more et/temp/solar = more risk
    signs = dict(zip(FEATURE_ORDER, S.SIGNS))
    assert signs["rainfall_anomaly"] < 0
    assert signs["soil_moisture"] < 0
    assert signs["ndvi_trend"] < 0
    assert signs["et"] > 0
    assert signs["temp_anomaly"] > 0
    assert signs["solar_radiation"] > 0
    assert S.WEIGHTS.sum() > 0


def test_drought_index_rises_as_conditions_dry_out():
    normal = np.zeros(len(FEATURE_ORDER))
    drier = normal.copy()
    drier[FEATURE_ORDER.index("rainfall_anomaly")] = -2.0  # 2 sigma below normal rain
    assert S.drought_index(drier) > S.drought_index(normal)


def test_index_to_score_is_monotonic_and_bounded():
    mu, sd = 0.0, 0.5
    lo = S.index_to_score(-1.5, mu, sd)
    mid = S.index_to_score(0.0, mu, sd)
    hi = S.index_to_score(1.5, mu, sd)
    assert 0 <= lo <= 100 and 0 <= hi <= 100
    assert lo < mid < hi
    # a season at the location's historical mean composite sits in the low band
    assert 30 <= mid <= 50


def test_contributions_pick_out_the_dry_driver():
    scaled = np.zeros(len(FEATURE_ORDER))
    scaled[FEATURE_ORDER.index("rainfall_anomaly")] = -2.0
    contrib = S.contributions(scaled)
    # the rainfall shortfall should be the single largest upward push on risk
    top = FEATURE_ORDER[int(np.argmax(contrib))]
    assert top == "rainfall_anomaly"
    assert contrib[FEATURE_ORDER.index("rainfall_anomaly")] > 0
