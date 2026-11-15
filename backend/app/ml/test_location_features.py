"""Tests for the per-location feature builder (real data, z-scored vs local)."""
from __future__ import annotations

import datetime as dt
import math

import numpy as np

from app.ml import location_features as LF
from app.ml.features import FEATURE_ORDER


def _synth_power(years, rain_by_year, gwet_by_year, lat=43.77):
    """NH-season (May-Oct) daily POWER payload with GWETROOT."""
    params = {k: {} for k in ("PRECTOTCORR", "T2M", "T2M_MAX", "T2M_MIN", "ALLSKY_SFC_SW_DWN", "GWETROOT")}
    for y in years:
        season_days = [
            dt.date(y, m, dd) for m in range(5, 11) for dd in range(1, 29)
        ]  # 6*28 = 168 days >= 120
        per_day_rain = rain_by_year[y] / len(season_days)
        for d in season_days:
            key = d.strftime("%Y%m%d")
            params["PRECTOTCORR"][key] = per_day_rain
            params["T2M"][key] = 24.0
            params["T2M_MAX"][key] = 30.0
            params["T2M_MIN"][key] = 18.0
            params["ALLSKY_SFC_SW_DWN"][key] = 20.0
            params["GWETROOT"][key] = gwet_by_year[y]
    return {"properties": {"parameter": params}, "geometry": {"coordinates": [11.26, lat, 0]}}


def _synth_modis(years, ndvi_by_year, scale=0.0001):
    subset = []
    for y in years:
        for m in (6, 8):  # a couple of in-season composites per year
            subset.append(
                {"calendar_date": f"{y}-{m:02d}-10", "data": [int(ndvi_by_year[y] / scale)]}
            )
    return {"subset": subset, "scale": scale}


def test_location_seasons_shapes_and_columns():
    years = [2020, 2021, 2022, 2023, 2024]
    power = _synth_power(
        years,
        rain_by_year={y: 600.0 for y in years},
        gwet_by_year={y: 0.4 for y in years},
    )
    modis = _synth_modis(years, {y: 0.5 for y in years})
    df = LF.location_seasons(power, modis, latitude=43.77, location="FL")
    assert set(df["year"]) == set(years)
    for col in ["location", "year", "seasonal_rainfall_mm", "soil_moisture_raw", "ndvi_mean", "et", "seasonal_tmean", "solar_radiation"]:
        assert col in df.columns
    assert not df["et"].isna().any()
    assert (df["et"] < 50).all()


def test_location_seasons_masks_fill_values():
    years = [2020, 2021, 2022, 2023, 2024]
    power = _synth_power(years, {y: 600.0 for y in years}, {y: 0.4 for y in years})
    # inject POWER fill
    power["properties"]["parameter"]["T2M"]["20200601"] = -999.0
    modis = _synth_modis(years, {y: 0.5 for y in years})
    # inject a MODIS fill observation
    modis["subset"].append({"calendar_date": "2024-07-10", "data": [-3000]})
    df = LF.location_seasons(power, modis, latitude=43.77, location="FL")
    assert not math.isnan(df.iloc[0]["seasonal_tmean"])
    assert not df["ndvi_mean"].isna().any()  # fill masked, not averaged in


def test_standardize_latest_returns_six_zscored_features_neutral():
    years = [2020, 2021, 2022, 2023, 2024]
    power = _synth_power(years, {y: 600.0 for y in years}, {y: 0.4 for y in years})
    modis = _synth_modis(years, {y: 0.5 for y in years})
    df = LF.location_seasons(power, modis, latitude=43.77, location="FL")
    feats = LF.standardize_latest(df)
    assert set(feats) == set(FEATURE_ORDER)
    for k, v in feats.items():
        assert abs(v) < 0.5, f"{k} should be ~neutral, got {v}"


def test_standardize_all_is_zscored_per_site():
    years = list(range(2010, 2024))
    rng = np.random.default_rng(1)
    rain = {y: float(600 + rng.normal(0, 60)) for y in years}
    gwet = {y: float(0.40 + rng.normal(0, 0.03)) for y in years}
    ndvi = {y: float(0.50 + rng.normal(0, 0.04)) for y in years}
    power = _synth_power(years, rain, gwet)
    modis = _synth_modis(years, ndvi)
    df = LF.location_seasons(power, modis, latitude=43.77, location="FL")
    std = LF.standardize_all(df)
    for col in FEATURE_ORDER + ["year", "location", "seasonal_rainfall_mm"]:
        assert col in std.columns
    assert len(std) == len(df)
    # per-site z-scored columns centre on ~0 with ~unit spread
    for col in ["soil_moisture", "ndvi_trend"]:
        assert abs(std[col].mean()) < 0.15
        assert abs(std[col].std(ddof=0) - 1.0) < 0.25


def _synth_sh_power(lat=-15.6):
    """Southern-hemisphere daily POWER from Jan 2005; the first season_year is a
    Jan-Apr fragment (no Nov/Dec head) that must be dropped (F3)."""
    params = {k: {} for k in ("PRECTOTCORR", "T2M", "T2M_MAX", "T2M_MIN", "ALLSKY_SFC_SW_DWN", "GWETROOT")}
    d, end = dt.date(2005, 1, 1), dt.date(2008, 12, 31)
    while d <= end:
        if d.month in (11, 12, 1, 2, 3, 4):
            k = d.strftime("%Y%m%d")
            params["PRECTOTCORR"][k] = 4.0
            params["T2M"][k] = 26.0
            params["T2M_MAX"][k] = 32.0
            params["T2M_MIN"][k] = 20.0
            params["ALLSKY_SFC_SW_DWN"][k] = 21.0
            params["GWETROOT"][k] = 0.35
        d += dt.timedelta(days=1)
    return {"properties": {"parameter": params}, "geometry": {"coordinates": [-47.8, lat, 0]}}


def test_sh_first_fragment_season_is_dropped():
    power = _synth_sh_power()
    df = LF.location_seasons(power, {"subset": [], "scale": 0.0001}, latitude=-15.6, location="BR")
    # season_year 2005 = only Jan-Apr 2005 (no Nov/Dec 2004) -> partial -> dropped
    assert 2005 not in set(df["year"])
    assert int(df["year"].min()) == 2006


def test_standardize_latest_matches_standardize_all_last_row():
    years = list(range(2010, 2024))
    rng = np.random.default_rng(7)
    rain = {y: float(600 + rng.normal(0, 60)) for y in years}
    gwet = {y: float(0.40 + rng.normal(0, 0.03)) for y in years}
    rain[2023], gwet[2023] = 250.0, 0.22  # anomalous latest -> where LOO vs full diverge
    power = _synth_power(years, rain, gwet)
    modis = _synth_modis(years, {y: 0.50 for y in years})
    df = LF.location_seasons(power, modis, latitude=43.77, location="FL")
    latest = LF.standardize_latest(df)
    last_row = LF.standardize_all(df).iloc[-1]
    for k in FEATURE_ORDER:
        assert abs(latest[k] - float(last_row[k])) < 1e-9, f"{k} inconsistent"


def test_drier_latest_year_pushes_features_negative():
    years = [2020, 2021, 2022, 2023, 2024]
    rain = {2020: 620, 2021: 600, 2022: 640, 2023: 610, 2024: 250}   # dry 2024
    gwet = {2020: 0.42, 2021: 0.40, 2022: 0.43, 2023: 0.41, 2024: 0.20}
    ndvi = {2020: 0.52, 2021: 0.50, 2022: 0.53, 2023: 0.51, 2024: 0.28}
    power = _synth_power(years, rain, gwet)
    modis = _synth_modis(years, ndvi)
    df = LF.location_seasons(power, modis, latitude=43.77, location="FL")
    feats = LF.standardize_latest(df)
    assert feats["rainfall_anomaly"] < 0
    assert feats["soil_moisture"] < 0
    assert feats["ndvi_trend"] < 0
