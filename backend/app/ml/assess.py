"""Per-location assessment orchestrator — OWNED BY THE `ml` AGENT.

`assess_location(lat, lon)` is the entry point the pipeline calls: it fetches a
location's NASA data (POWER + MODIS, cache-first so a warmed point needs no
network), builds the season table, and returns the six standardized features
ready for `predict_risk`. No training, no heavy work — fast once cached.
"""
from __future__ import annotations

import math

from . import data as D
from .location_features import location_seasons, standardize_latest

_RAW_COLS = ["seasonal_rainfall_mm", "soil_moisture_raw", "ndvi_mean", "et", "seasonal_tmean", "solar_radiation"]


class NoDataError(RuntimeError):
    """Raised when a coordinate has no usable land/season data (e.g. ocean)."""


def assess_location(lat: float, lon: float, cache_dir=D.DEFAULT_CACHE_DIR, with_ndvi: bool = True) -> dict:
    """Return the six model features (z-scores vs local normal) for this point.

    Raises NoDataError for coordinates with no usable seasons (ocean/no-data).
    `with_ndvi=False` skips MODIS (ndvi_trend stays neutral, as in training) so a
    live request is a single cache-first POWER read, not ~51 chunked MODIS calls.
    """
    start, end = D.history_range()
    power = D.fetch_power(lat, lon, start, end, cache_dir=cache_dir)
    if with_ndvi:
        modis = D.fetch_modis_ndvi(lat, lon, start, end, cache_dir=cache_dir)
    else:
        modis = {"subset": [], "scale": 0.0001}

    seasons = location_seasons(power, modis, lat, f"{lat},{lon}")
    if len(seasons) < 2:
        raise NoDataError(f"no usable NASA seasons at ({lat}, {lon})")

    feats = standardize_latest(seasons)
    latest = seasons.iloc[-1]

    def _jsafe(v):
        v = float(v)
        return v if math.isfinite(v) else None  # keep _meta valid JSON (no NaN)

    feats["_meta"] = {
        "latitude": lat,
        "longitude": lon,
        "data_mode": "live",
        "n_seasons": int(len(seasons)),
        "latest_season_year": int(latest["year"]),
        "raw": {c: _jsafe(latest[c]) for c in _RAW_COLS},
    }
    return feats


def prewarm(coords) -> None:
    """Fetch + cache each coordinate so a later live demo never stalls."""
    for lat, lon in coords:
        try:
            assess_location(lat, lon)
        except NoDataError:
            pass
