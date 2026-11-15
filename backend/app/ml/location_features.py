"""Per-location feature builder — OWNED BY THE `ml` AGENT.

Turns a location's raw NASA data (POWER daily + MODIS NDVI) into the six model
features for the latest growing season, expressed as **standardized anomalies
vs that location's own history** (z-scores; 0 = local normal). Because every
feature is relative to the place's own past, the same model works anywhere on
Earth — this is what makes Field Shift global and fixes the Florence bug.

Season is hemisphere-aware: Northern Hemisphere grows May-Oct, Southern Nov-Apr.
Soil moisture is real (POWER GWETROOT), NDVI is real (MODIS) — no more proxies.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .features import FEATURE_ORDER, POWER_FILL, extraterrestrial_radiation, hargreaves_et0
from .spi import spi_latest, spi_series

NH_SEASON = (5, 6, 7, 8, 9, 10)       # Northern Hemisphere rainfed growing season
SH_SEASON = (11, 12, 1, 2, 3, 4)      # Southern Hemisphere (crosses the new year)
MODIS_FILL = -3000                    # MODIS NDVI fill sentinel


def growing_season(latitude: float):
    return NH_SEASON if latitude >= 0 else SH_SEASON


def _season_year(dt_index: pd.DatetimeIndex, latitude: float) -> np.ndarray:
    """Calendar year the season belongs to. SH Nov/Dec roll into the next year."""
    years = dt_index.year.to_numpy().copy()
    if latitude < 0:
        nov_dec = np.isin(dt_index.month, [11, 12])
        years = np.where(nov_dec, years + 1, years)
    return years


def _modis_season_ndvi(modis_json: dict, latitude: float) -> dict:
    """season_year -> mean in-season NDVI (fill masked)."""
    subs = modis_json.get("subset", [])
    scale = float(modis_json.get("scale", 0.0001) or 0.0001)
    dates, vals = [], []
    for s in subs:
        data = s.get("data") or []
        if not data:
            continue
        dates.append(s["calendar_date"])
        vals.append(float(data[0]))
    if not dates:
        return {}
    idx = pd.to_datetime(dates)
    v = pd.Series(vals, index=idx)
    v = v.where(v != MODIS_FILL) * scale
    season = set(growing_season(latitude))
    in_season = v[idx.month.isin(season)].dropna()
    if in_season.empty:
        return {}
    sy = _season_year(in_season.index, latitude)
    return pd.DataFrame({"ndvi": in_season.to_numpy(), "sy": sy}).groupby("sy")["ndvi"].mean().to_dict()


def location_seasons(power_json: dict, modis_json: dict, latitude: float, location: str) -> pd.DataFrame:
    """One row per season-complete year with the raw seasonal aggregates."""
    params = power_json["properties"]["parameter"]
    frames = {}
    for name, series in params.items():
        s = pd.Series(series, dtype=float)
        s.index = pd.to_datetime(s.index, format="%Y%m%d")
        frames[name] = s
    df = pd.DataFrame(frames).sort_index().replace(POWER_FILL, np.nan)

    season = set(growing_season(latitude))
    df = df[df.index.month.isin(season)]

    ra = np.array([extraterrestrial_radiation(latitude, int(d.dayofyear)) for d in df.index])
    et0 = np.array(
        [
            hargreaves_et0(tn, tx, r) if np.isfinite(tn) and np.isfinite(tx) else np.nan
            for tn, tx, r in zip(df["T2M_MIN"], df["T2M_MAX"], ra)
        ]
    )
    df = df.assign(_et0=et0, _sy=_season_year(df.index, latitude))

    ndvi_by = _modis_season_ndvi(modis_json, latitude)

    season_months = set(growing_season(latitude))
    rows = []
    for sy, g in df.groupby("_sy"):
        # drop partial head/tail seasons (esp. the first SH Jan-Apr fragment):
        # the whole growing season must be present
        if not season_months.issubset(set(g.index.month)):
            continue
        if g["PRECTOTCORR"].notna().sum() < 120:
            continue
        # reject non-land points: GWETROOT (soil moisture) is land-only; over
        # ocean POWER fills it, so without it this isn't a farmable location
        if g["GWETROOT"].notna().sum() < 120:
            continue
        rows.append(
            {
                "location": location,
                "year": int(sy),
                "seasonal_rainfall_mm": float(g["PRECTOTCORR"].sum()),
                "soil_moisture_raw": float(np.nanmean(g["GWETROOT"])),
                "ndvi_mean": float(ndvi_by.get(int(sy), np.nan)),
                "et": float(np.nanmean(g["_et0"])),
                "seasonal_tmean": float(g["T2M"].mean()),
                "solar_radiation": float(g["ALLSKY_SFC_SW_DWN"].mean()),
            }
        )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values("year").reset_index(drop=True)


def standardize_latest(seasons: pd.DataFrame) -> dict:
    """The six model features for the LATEST season, as z-scores vs local normal.

    Derived from `standardize_all` (its last row) so inference uses the EXACT
    same full-column standardization the model was trained on. Keys match
    FEATURE_ORDER; sign convention (see scoring.SIGNS): negative rainfall/soil/
    ndvi = drier/worse; positive et/temp/solar = more stress.
    """
    if len(seasons) < 2:
        raise ValueError("need >= 2 seasons to standardize against history")
    last = standardize_all(seasons).iloc[-1]
    return {name: float(last[name]) for name in FEATURE_ORDER}


_RAW_FOR = {
    "soil_moisture": "soil_moisture_raw",
    "ndvi_trend": "ndvi_mean",
    "et": "et",
    "temp_anomaly": "seasonal_tmean",
    "solar_radiation": "solar_radiation",
}


def _zcol(series) -> np.ndarray:
    """z-score a whole column vs its own distribution (noise-floored; NaN->0)."""
    s = np.asarray(series, dtype=float)
    finite = s[np.isfinite(s)]
    if finite.size < 2:
        return np.zeros(s.size)
    mean, std = finite.mean(), finite.std()
    if std < 1e-9 or std < 5e-3 * (abs(mean) + 1e-9):
        return np.zeros(s.size)
    z = (s - mean) / std
    return np.where(np.isfinite(z), z, 0.0)


def standardize_all(seasons: pd.DataFrame) -> pd.DataFrame:
    """Every season as z-scored features vs the site's own history (for training).

    Like standardize_latest but for all rows; rainfall is per-season SPI. Keeps
    `location`, `year`, `seasonal_rainfall_mm` for labelling downstream.
    """
    if len(seasons) < 2:
        raise ValueError("need >= 2 seasons to standardize against history")
    out = pd.DataFrame(
        {
            "location": seasons["location"].to_numpy(),
            "year": seasons["year"].to_numpy(),
            "seasonal_rainfall_mm": seasons["seasonal_rainfall_mm"].to_numpy(),
            "rainfall_anomaly": spi_series(seasons["seasonal_rainfall_mm"].tolist()),
        }
    )
    for feat, raw in _RAW_FOR.items():
        out[feat] = _zcol(seasons[raw])
    return out[["location", "year", "seasonal_rainfall_mm"] + FEATURE_ORDER]
