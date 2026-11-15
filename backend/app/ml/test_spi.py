"""Tests for the SPI (Standardized Precipitation Index) module."""
from __future__ import annotations

from app.ml import spi as S


def test_accumulate_sums_consecutive_windows():
    # 12 months, 3-month window -> rolling 3-month sums
    monthly = [1.0] * 12
    sums = S.accumulate(monthly, 3)
    assert sums[-1] == 3.0
    assert len(sums) == 10  # 12 - 3 + 1


def test_spi_dry_window_is_negative():
    # history of ~normal totals, last value clearly low -> strongly negative SPI
    totals = [100.0, 110.0, 95.0, 105.0, 120.0, 98.0, 102.0, 115.0, 108.0, 30.0]
    assert S.spi_latest(totals) < -1.0


def test_spi_wet_window_is_positive():
    totals = [100.0, 110.0, 95.0, 105.0, 120.0, 98.0, 102.0, 115.0, 108.0, 230.0]
    assert S.spi_latest(totals) > 1.0


def test_spi_median_near_zero():
    totals = [100.0, 110.0, 95.0, 105.0, 120.0, 98.0, 102.0, 115.0, 108.0, 104.0]
    assert abs(S.spi_latest(totals)) < 0.6


def test_spi_all_zero_is_finite_and_not_positive():
    totals = [0.0] * 10
    v = S.spi_latest(totals)
    assert v == v  # not NaN
    assert v <= 0.0
    assert v > -10.0  # finite floor


def test_spi_series_matches_latest_and_signs():
    totals = [100.0, 110.0, 95.0, 105.0, 120.0, 98.0, 102.0, 115.0, 108.0, 40.0]
    series = S.spi_series(totals)
    assert len(series) == len(totals)
    assert abs(series[-1] - S.spi_latest(totals)) < 1e-9  # last element == spi_latest
    assert series[-1] < -1.0  # the dry last year reads dry


def test_spi_short_history_falls_back_to_normal_approx():
    # < 8 points: still returns a finite, correctly-signed z-score
    totals = [100.0, 110.0, 90.0, 40.0]
    v = S.spi_latest(totals)
    assert v == v and v < 0  # the low last value reads dry
