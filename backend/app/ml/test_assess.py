"""Tests for assess_location — the per-location entry point (no network)."""
from __future__ import annotations

import datetime as dt

import pytest

from app.ml import assess as A
from app.ml import data as D
from app.ml.features import FEATURE_ORDER


def _synth_power(dry_latest=False):
    years = [2020, 2021, 2022, 2023, 2024]
    # realistic inter-annual spread in the history (every real location has it)
    rain_by = {2020: 620.0, 2021: 590.0, 2022: 635.0, 2023: 600.0, 2024: 605.0}
    gwet_by = {2020: 0.42, 2021: 0.39, 2022: 0.43, 2023: 0.40, 2024: 0.41}
    if dry_latest:
        rain_by[2024], gwet_by[2024] = 250.0, 0.20
    params = {k: {} for k in ("PRECTOTCORR", "T2M", "T2M_MAX", "T2M_MIN", "ALLSKY_SFC_SW_DWN", "GWETROOT")}
    for y in years:
        rain = rain_by[y]
        gwet = gwet_by[y]
        days = [dt.date(y, m, dd) for m in range(5, 11) for dd in range(1, 29)]
        for d in days:
            k = d.strftime("%Y%m%d")
            params["PRECTOTCORR"][k] = rain / len(days)
            params["T2M"][k] = 24.0 + (y - 2022) * 0.3
            params["T2M_MAX"][k] = 30.0
            params["T2M_MIN"][k] = 18.0
            params["ALLSKY_SFC_SW_DWN"][k] = 20.0 + (y - 2022) * 0.2
            params["GWETROOT"][k] = gwet
    return {"properties": {"parameter": params}, "geometry": {"coordinates": [11.26, 43.77, 0]}}


def _synth_modis():
    years = [2020, 2021, 2022, 2023, 2024]
    return {"subset": [{"calendar_date": f"{y}-06-10", "data": [5000]} for y in years], "scale": 0.0001}


def _all_fill_power():
    params = {k: {"20200601": -999.0} for k in ("PRECTOTCORR", "T2M", "T2M_MAX", "T2M_MIN", "ALLSKY_SFC_SW_DWN", "GWETROOT")}
    return {"properties": {"parameter": params}, "geometry": {"coordinates": [0, 0, 0]}}


def test_assess_returns_six_features_in_range(monkeypatch):
    monkeypatch.setattr(D, "fetch_power", lambda *a, **k: _synth_power())
    monkeypatch.setattr(D, "fetch_modis_ndvi", lambda *a, **k: _synth_modis())
    out = A.assess_location(43.77, 11.26)
    assert set(out) - {"_meta"} == set(FEATURE_ORDER)
    for name in FEATURE_ORDER:
        assert isinstance(out[name], float) and out[name] == out[name]  # finite, not NaN
    assert out["_meta"]["data_mode"] == "live"


def test_assess_uses_cached_fetchers(monkeypatch):
    calls = {"power": 0, "modis": 0}

    def fp(*a, **k):
        calls["power"] += 1
        return _synth_power()

    def fm(*a, **k):
        calls["modis"] += 1
        return _synth_modis()

    monkeypatch.setattr(D, "fetch_power", fp)
    monkeypatch.setattr(D, "fetch_modis_ndvi", fm)
    A.assess_location(43.77, 11.26)
    # goes through the cache-first data layer, not raw requests
    assert calls["power"] == 1 and calls["modis"] == 1


def test_assess_dry_location_reads_negative(monkeypatch):
    monkeypatch.setattr(D, "fetch_power", lambda *a, **k: _synth_power(dry_latest=True))
    monkeypatch.setattr(D, "fetch_modis_ndvi", lambda *a, **k: _synth_modis())
    out = A.assess_location(43.77, 11.26)
    assert out["rainfall_anomaly"] < 0 and out["soil_moisture"] < 0


def test_assess_raises_on_no_data(monkeypatch):
    monkeypatch.setattr(D, "fetch_power", lambda *a, **k: _all_fill_power())
    monkeypatch.setattr(D, "fetch_modis_ndvi", lambda *a, **k: {"subset": [], "scale": 0.0001})
    with pytest.raises(A.NoDataError):
        A.assess_location(0.0, 0.0)


def _ocean_power():
    # over ocean POWER still returns valid precip/temp but GWETROOT (land-only)
    # is all fill -> a drought read here would be nonsense (F1)
    years = [2020, 2021, 2022, 2023, 2024]
    params = {k: {} for k in ("PRECTOTCORR", "T2M", "T2M_MAX", "T2M_MIN", "ALLSKY_SFC_SW_DWN", "GWETROOT")}
    for y in years:
        for d in [dt.date(y, m, dd) for m in range(5, 11) for dd in range(1, 29)]:
            k = d.strftime("%Y%m%d")
            params["PRECTOTCORR"][k] = 3.0
            params["T2M"][k] = 20.0
            params["T2M_MAX"][k] = 22.0
            params["T2M_MIN"][k] = 18.0
            params["ALLSKY_SFC_SW_DWN"][k] = 20.0
            params["GWETROOT"][k] = -999.0  # land-only fill
    return {"properties": {"parameter": params}, "geometry": {"coordinates": [-30.0, 0.0, 0]}}


def test_assess_ocean_coordinate_raises_no_data(monkeypatch):
    monkeypatch.setattr(D, "fetch_power", lambda *a, **k: _ocean_power())
    monkeypatch.setattr(D, "fetch_modis_ndvi", lambda *a, **k: {"subset": [], "scale": 0.0001})
    with pytest.raises(A.NoDataError):
        A.assess_location(0.0, -30.0)


def test_assess_meta_raw_is_json_safe_without_ndvi(monkeypatch):
    import json

    # no MODIS composite -> ndvi_mean is NaN; _meta.raw must stay JSON-valid (F2)
    monkeypatch.setattr(D, "fetch_power", lambda *a, **k: _synth_power())
    monkeypatch.setattr(D, "fetch_modis_ndvi", lambda *a, **k: {"subset": [], "scale": 0.0001})
    out = A.assess_location(43.77, 11.26)
    assert out["_meta"]["raw"]["ndvi_mean"] is None
    json.dumps(out["_meta"], allow_nan=False)  # must not raise on a NaN
