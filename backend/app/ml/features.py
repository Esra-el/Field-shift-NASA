"""Feature engineering for the drought-risk model — OWNED BY THE `ml` AGENT.

Pure, deterministic, NO network. Everything here can be unit-tested with plain
arrays, which is why the NASA-POWER fetch lives separately in `data.py`.

The model's six features (fixed order, matches `risk.predict_risk`):

    rainfall_anomaly   (recent - normal) / normal     negative = drier
    soil_moisture      m3/m3  (~0.05..0.45)            PROXY at train time (see below)
    ndvi_trend         slope of greenness             PROXY at train time (see below)
    et                 Hargreaves ET0, mm/day
    temp_anomaly       seasonal mean T2M - climatology, deg C
    solar_radiation    ALLSKY_SFC_SW_DWN, MJ/m2/day

Two of those six are NOT in NASA POWER:
  * soil_moisture  -> real source would be SMAP / in-situ sensors
  * ndvi_trend     -> real source would be MODIS / VIIRS NDVI
For TRAINING ONLY we substitute documented climate proxies (see the two
`*_proxy` functions). At inference the pipeline passes the real values straight
through `feature_vector`; the proxies are never used to answer a live request.
"""
from __future__ import annotations

import math
from typing import Iterable

import numpy as np
import pandas as pd

# The feature contract. Order matters: it is the column order of every matrix
# and the index order of every vector the model ever sees.
FEATURE_ORDER = [
    "rainfall_anomaly",
    "soil_moisture",
    "ndvi_trend",
    "et",
    "temp_anomaly",
    "solar_radiation",
]

# Features are standardized anomalies vs the location's own normal (z-scores;
# 0 = exactly normal). So every omitted feature defaults to 0.0 = "no signal".
FEATURE_DEFAULTS = {name: 0.0 for name in FEATURE_ORDER}

# Main rain-fed growing season for the Central American Dry Corridor
# (primera + canicula + postrera). Seasonal totals are built over these months.
SEASON_MONTHS = (5, 6, 7, 8, 9, 10)

# NASA POWER marks missing data with this sentinel; it must become NaN.
POWER_FILL = -999.0


# --------------------------------------------------------------------------- #
# Evapotranspiration (Hargreaves-Samani, FAO-56)
# --------------------------------------------------------------------------- #
def extraterrestrial_radiation(latitude_deg: float, doy: int) -> float:
    """Ra, top-of-atmosphere radiation (MJ/m2/day), FAO-56 eq. 21-25.

    Depends only on latitude and day-of-year, so it needs no measured data.
    """
    phi = math.radians(latitude_deg)
    dr = 1.0 + 0.033 * math.cos(2.0 * math.pi * doy / 365.0)       # inverse rel. distance
    decl = 0.409 * math.sin(2.0 * math.pi * doy / 365.0 - 1.39)    # solar declination
    # sunset hour angle (clamp the arccos argument for polar edge cases)
    x = -math.tan(phi) * math.tan(decl)
    x = max(-1.0, min(1.0, x))
    ws = math.acos(x)
    gsc = 0.0820  # solar constant, MJ/m2/min
    ra = (24.0 * 60.0 / math.pi) * gsc * dr * (
        ws * math.sin(phi) * math.sin(decl)
        + math.cos(phi) * math.cos(decl) * math.sin(ws)
    )
    return ra


def hargreaves_et0(tmin: float, tmax: float, ra_mj: float) -> float:
    """Reference ET0 (mm/day). FAO-56 Hargreaves: needs only Tmin/Tmax + Ra."""
    tmean = (tmax + tmin) / 2.0
    ra_mm = 0.408 * ra_mj                       # MJ/m2/day -> mm/day equivalent
    tr = max(0.0, tmax - tmin)
    return 0.0023 * (tmean + 17.8) * math.sqrt(tr) * ra_mm


# --------------------------------------------------------------------------- #
# Training-only proxies (documented stand-ins; never used at inference)
# --------------------------------------------------------------------------- #
def soil_moisture_proxy(water_balance_mm: Iterable[float]) -> np.ndarray:
    """PROXY soil moisture from a seasonal water balance (P - ET, mm).

    Standardize the balance across a location's history and squash it into a
    plausible volumetric range (0.05..0.45 m3/m3). Wetter balance -> wetter soil.
    This is a climate surrogate, NOT a measurement; the real pipeline uses SMAP.
    """
    bal = np.asarray(list(water_balance_mm), dtype=float)
    std = bal.std()
    z = (bal - bal.mean()) / std if std > 1e-9 else np.zeros_like(bal)
    squashed = 1.0 / (1.0 + np.exp(-z))         # logistic -> (0, 1)
    return 0.05 + 0.40 * squashed


def ndvi_trend_proxy(rainfall_anomaly: Iterable[float]) -> np.ndarray:
    """PROXY NDVI trend from the rainfall anomaly.

    Rain-fed greenness tracks water with a lag: a wetter-than-normal season
    greens up (+slope), a drier one browns off (-slope). Scaled to a realistic
    NDVI slope band (~+/-0.2). Real pipeline uses MODIS/VIIRS NDVI.
    """
    anom = np.asarray(list(rainfall_anomaly), dtype=float)
    return 0.2 * np.tanh(anom * 2.0)


# --------------------------------------------------------------------------- #
# dict -> ordered vector (the inference entry)
# --------------------------------------------------------------------------- #
def feature_vector(features: dict) -> np.ndarray:
    """Turn an inbound feature dict into the ordered float vector the model uses.

    Missing keys fall back to neutral "seasonal normal" defaults so a partial
    payload never crashes a live request.
    """
    return np.array(
        [float(features.get(name, FEATURE_DEFAULTS[name])) for name in FEATURE_ORDER],
        dtype=float,
    )


# --------------------------------------------------------------------------- #
# NASA POWER payload -> per-season feature rows
# --------------------------------------------------------------------------- #
def _daily_frame(power_json: dict) -> pd.DataFrame:
    """Parse a POWER daily payload into a tidy daily DataFrame (fills -> NaN)."""
    params = power_json["properties"]["parameter"]
    frames = {}
    for name, series in params.items():
        s = pd.Series(series, dtype=float)
        s.index = pd.to_datetime(s.index, format="%Y%m%d")
        frames[name] = s
    df = pd.DataFrame(frames).sort_index()
    df = df.replace(POWER_FILL, np.nan)
    return df


def build_feature_matrix(power_json: dict, latitude_deg: float, location: str) -> pd.DataFrame:
    """One row per season-complete year for a single location.

    Anomalies are computed against that location's own climatology (the mean
    over the available years), which is how a farmer actually experiences
    "drier than usual here" rather than "drier than some global average".
    """
    df = _daily_frame(power_json)
    df = df[df.index.month.isin(SEASON_MONTHS)]

    # per-day ET0 (Hargreaves) so the seasonal ET reflects day-to-day heat
    ra = np.array([extraterrestrial_radiation(latitude_deg, int(d.dayofyear)) for d in df.index])
    et0 = np.array(
        [
            hargreaves_et0(tmin, tmax, r)
            if np.isfinite(tmin) and np.isfinite(tmax)
            else np.nan
            for tmin, tmax, r in zip(df["T2M_MIN"], df["T2M_MAX"], ra)
        ]
    )
    df = df.assign(_et0=et0)

    rows = []
    for year, g in df.groupby(df.index.year):
        # require a reasonably complete season before trusting the aggregates
        if g["PRECTOTCORR"].notna().sum() < 120:
            continue
        rows.append(
            {
                "location": location,
                "year": int(year),
                "seasonal_rainfall_mm": float(g["PRECTOTCORR"].sum()),
                "seasonal_tmean": float(g["T2M"].mean()),
                "et": float(np.nanmean(g["_et0"])),
                "solar_radiation": float(g["ALLSKY_SFC_SW_DWN"].mean()),
            }
        )

    out = pd.DataFrame(rows).sort_values("year").reset_index(drop=True)
    if out.empty:
        return out

    # location climatology -> anomalies
    rain_clim = out["seasonal_rainfall_mm"].mean()
    temp_clim = out["seasonal_tmean"].mean()
    out["rainfall_anomaly"] = (out["seasonal_rainfall_mm"] - rain_clim) / rain_clim
    out["temp_anomaly"] = out["seasonal_tmean"] - temp_clim

    # documented proxies for the two non-POWER features
    water_balance = out["seasonal_rainfall_mm"] - out["et"] * len(SEASON_MONTHS) * 30.0
    out["soil_moisture"] = soil_moisture_proxy(water_balance.to_numpy())
    out["ndvi_trend"] = ndvi_trend_proxy(out["rainfall_anomaly"].to_numpy())

    return out
