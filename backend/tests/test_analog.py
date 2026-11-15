"""Tests for the 20-year same-date POWER analog (app/ml/analog.py).

Hermetic: no network. We monkeypatch the POWER fetch with a synthetic 20-year
daily record and check the analog reacts correctly — a dry current year reads as
high drought risk, a wet one does not, and missing data degrades gracefully.
"""
import datetime as dt

import pytest

from app.ml import analog


@pytest.fixture(autouse=True)
def _clear_analog_cache():
    # The module caches per point+date in memory; isolate tests so one fixture's
    # result can't be served to the next test (same coordinate/date key).
    analog._MEM.clear()
    yield
    analog._MEM.clear()


def _synthetic_power(current_rain_mm_day: float, hist_rain_mm_day: float = 3.0) -> dict:
    """2006..2026 daily POWER, constant per-day values; current year (2026) rain overridden."""
    params = {"PRECTOTCORR": {}, "T2M": {}, "GWETROOT": {}, "ALLSKY_SFC_SW_DWN": {}}
    for y in range(2006, 2027):
        d = dt.date(y, 1, 1)
        while d.year == y:
            k = d.strftime("%Y%m%d")
            params["PRECTOTCORR"][k] = current_rain_mm_day if y == 2026 else hist_rain_mm_day
            params["T2M"][k] = 26.0
            params["GWETROOT"][k] = 0.30
            params["ALLSKY_SFC_SW_DWN"][k] = 20.0
            d += dt.timedelta(days=1)
    return {"properties": {"parameter": params}}


TODAY = dt.date(2026, 11, 15)


def test_dry_current_year_reads_as_high_risk(monkeypatch):
    # Current year far drier than the 20-year history for this date -> high risk.
    monkeypatch.setattr(analog.power_data, "fetch_power", lambda *a, **k: _synthetic_power(0.2))
    r = analog.analog(14.8, -90.5, today=TODAY)
    assert r["source"] == "power_analog"
    assert r["n_years"] >= 15                       # used ~20 years of same-date data
    assert r["rain_percentile"] <= 0.15             # among the driest for this date
    assert r["risk_level"] == "high" and r["risk_score"] >= 70
    assert any("driest" in d for d in r["drivers"])


def test_wet_current_year_is_not_high_risk(monkeypatch):
    # Current year clearly wetter than history -> low drought risk.
    monkeypatch.setattr(analog.power_data, "fetch_power", lambda *a, **k: _synthetic_power(6.0))
    r = analog.analog(14.8, -90.5, today=TODAY)
    assert r["source"] == "power_analog"
    assert r["rain_percentile"] >= 0.85
    assert r["risk_level"] == "low"


def test_normal_year_is_middle(monkeypatch):
    # Current == history for this date -> mid-rank percentile ~0.5, not an extreme.
    monkeypatch.setattr(analog.power_data, "fetch_power", lambda *a, **k: _synthetic_power(3.0))
    r = analog.analog(14.8, -90.5, today=TODAY)
    assert 0.35 <= r["rain_percentile"] <= 0.65
    assert r["risk_level"] != "high"


def test_headline_is_localized_and_cites_nasa(monkeypatch):
    monkeypatch.setattr(analog.power_data, "fetch_power", lambda *a, **k: _synthetic_power(0.2))
    r = analog.analog(14.8, -90.5, today=TODAY)
    h_en, h_fr = analog.headline(r, "en"), analog.headline(r, "fr")
    assert "NASA POWER" in h_en and "20" in h_en and "driest" in h_en.lower()
    assert "NASA POWER" in h_fr and "secs" in h_fr.lower()
    assert analog.headline({"source": "unavailable"}, "en") == ""


def test_unavailable_on_empty_power(monkeypatch):
    monkeypatch.setattr(analog.power_data, "fetch_power", lambda *a, **k: {"properties": {"parameter": {}}})
    assert analog.analog(0.0, 0.0, today=TODAY) == {"source": "unavailable"}


def test_never_raises_on_broken_fetch(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("network down")
    monkeypatch.setattr(analog.power_data, "fetch_power", boom)
    assert analog.analog(14.8, -90.5, today=TODAY)["source"] == "unavailable"
