"""Tests for the pure feature-engineering layer (no network).

Covers the physics/math pieces the model is built on:
  * Hargreaves reference evapotranspiration (ET0) and extraterrestrial radiation
  * feature_vector(): dict -> ordered array with sane defaults
  * documented training-only proxies (soil moisture, NDVI trend)
  * build_feature_matrix(): parse a NASA-POWER-shaped JSON into per-season rows
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from app.ml import features as F


# --------------------------------------------------------------------------- #
# Hargreaves ET0 + extraterrestrial radiation
# --------------------------------------------------------------------------- #
def test_extraterrestrial_radiation_equator_is_high():
    # Near the equator around equinox, Ra peaks around ~36-38 MJ/m2/day.
    ra = F.extraterrestrial_radiation(latitude_deg=0.0, doy=80)
    assert 34.0 <= ra <= 39.0


def test_hargreaves_et0_matches_hand_computation():
    # Tmean=24, Tmax=30, Tmin=18, Ra=37 MJ/m2/day
    #   Ra_mm = 0.408 * 37 = 15.1
    #   ET0  = 0.0023 * (24+17.8) * sqrt(12) * 15.1 ~= 5.0 mm/day
    et0 = F.hargreaves_et0(tmin=18.0, tmax=30.0, ra_mj=37.0)
    assert et0 == pytest.approx(5.0, abs=0.3)


def test_hargreaves_et0_rises_with_heat():
    cool = F.hargreaves_et0(tmin=16.0, tmax=24.0, ra_mj=35.0)
    hot = F.hargreaves_et0(tmin=20.0, tmax=38.0, ra_mj=35.0)
    assert hot > cool


# --------------------------------------------------------------------------- #
# feature_vector: dict -> ordered array
# --------------------------------------------------------------------------- #
def test_feature_order_is_the_contract():
    assert F.FEATURE_ORDER == [
        "rainfall_anomaly",
        "soil_moisture",
        "ndvi_trend",
        "et",
        "temp_anomaly",
        "solar_radiation",
    ]


def test_feature_vector_respects_order_and_values():
    vec = F.feature_vector(
        {
            "rainfall_anomaly": -0.3,
            "soil_moisture": 0.12,
            "ndvi_trend": -0.08,
            "et": 5.5,
            "temp_anomaly": 1.2,
            "solar_radiation": 22.0,
        }
    )
    assert vec.shape == (6,)
    assert vec.tolist() == [-0.3, 0.12, -0.08, 5.5, 1.2, 22.0]


def test_feature_vector_fills_missing_with_neutral_defaults():
    vec = F.feature_vector({})
    # neutral season: no anomaly, mid soil moisture, flat vegetation
    assert vec[F.FEATURE_ORDER.index("rainfall_anomaly")] == 0.0
    assert vec[F.FEATURE_ORDER.index("ndvi_trend")] == 0.0
    assert vec[F.FEATURE_ORDER.index("temp_anomaly")] == 0.0
    assert 0.2 <= vec[F.FEATURE_ORDER.index("soil_moisture")] <= 0.3


# --------------------------------------------------------------------------- #
# Documented training-only proxies
# --------------------------------------------------------------------------- #
def test_soil_moisture_proxy_wetter_balance_gives_more_moisture():
    bal = np.array([-100.0, 0.0, 120.0])  # P-ET surplus across a location's years
    sm = F.soil_moisture_proxy(bal)
    assert sm.shape == (3,)
    assert (sm >= 0.05).all() and (sm <= 0.45).all()
    assert sm[2] > sm[1] > sm[0]  # wetter -> more soil moisture


def test_ndvi_trend_proxy_tracks_rainfall_anomaly_sign():
    anom = np.array([-0.4, 0.0, 0.3])
    ndvi = F.ndvi_trend_proxy(anom)
    assert ndvi[0] < 0 < ndvi[2]       # drier -> browning, wetter -> greening
    assert abs(ndvi).max() <= 0.25     # kept in a realistic slope range


# --------------------------------------------------------------------------- #
# build_feature_matrix on a synthetic POWER-shaped payload
# --------------------------------------------------------------------------- #
def _synthetic_power(years, rain_by_year, lat=14.8):
    """Minimal NASA POWER daily JSON: one dry year and one wet year."""
    params = {
        "PRECTOTCORR": {},
        "T2M": {},
        "T2M_MAX": {},
        "T2M_MIN": {},
        "ALLSKY_SFC_SW_DWN": {},
    }
    import datetime as dt

    for y in years:
        d = dt.date(y, 1, 1)
        end = dt.date(y, 12, 31)
        # distribute that year's rain only across the May-Oct season
        season_days = [
            dt.date(y, m, dd)
            for m in range(5, 11)
            for dd in range(1, 29)
        ]
        per_day_rain = rain_by_year[y] / len(season_days)
        while d <= end:
            key = d.strftime("%Y%m%d")
            in_season = 5 <= d.month <= 10
            params["PRECTOTCORR"][key] = per_day_rain if in_season else 0.0
            params["T2M"][key] = 24.0
            params["T2M_MAX"][key] = 30.0
            params["T2M_MIN"][key] = 18.0
            params["ALLSKY_SFC_SW_DWN"][key] = 20.0
            d += dt.timedelta(days=1)
    return {"properties": {"parameter": params}, "geometry": {"coordinates": [-90.5, lat, 0]}}


def test_build_feature_matrix_shapes_and_anomaly_sign():
    payload = _synthetic_power(
        years=[2010, 2011], rain_by_year={2010: 400.0, 2011: 1200.0}, lat=14.8
    )
    df = F.build_feature_matrix(payload, latitude_deg=14.8, location="GT")

    # one row per season-complete year
    assert set(df["year"]) == {2010, 2011}
    for col in F.FEATURE_ORDER + ["year", "location", "seasonal_rainfall_mm"]:
        assert col in df.columns

    dry = df[df["year"] == 2010].iloc[0]
    wet = df[df["year"] == 2011].iloc[0]
    # dry year: rainfall below the 2-year mean -> negative anomaly; wet year positive
    assert dry["rainfall_anomaly"] < 0 < wet["rainfall_anomaly"]
    # proxies follow: dry year has lower soil moisture and browning vegetation
    assert dry["soil_moisture"] < wet["soil_moisture"]
    assert dry["ndvi_trend"] < wet["ndvi_trend"]
    # ET should be a sane tropical value
    assert 3.0 <= dry["et"] <= 8.0


def test_build_feature_matrix_masks_power_fill_values():
    payload = _synthetic_power(years=[2010], rain_by_year={2010: 600.0})
    # inject a POWER fill sentinel; it must not poison the mean
    payload["properties"]["parameter"]["T2M"]["20100601"] = -999.0
    df = F.build_feature_matrix(payload, latitude_deg=14.8, location="GT")
    assert not math.isnan(df.iloc[0]["temp_anomaly"])
    assert df.iloc[0]["et"] < 50  # -999 would have blown this up
