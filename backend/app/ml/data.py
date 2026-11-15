"""NASA POWER data access — OWNED BY THE `ml` AGENT.

The ONLY module that touches the network, and only at train time. Every raw
response is cached to app/data/cache/ so the model can be rebuilt — and the
demo can run — with no live API dependency.

NASA POWER daily point API (no auth):
  https://power.larc.nasa.gov/api/temporal/daily/point
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path

# Daily variables we pull. PRECTOTCORR (rain), T2M/MAX/MIN (temperature),
# ALLSKY_SFC_SW_DWN (solar), GWETROOT/GWETTOP (root-zone/surface soil wetness —
# real soil moisture, retires the proxy), RH2M/WS2M for water-balance work.
POWER_PARAMETERS = "PRECTOTCORR,T2M,T2M_MAX,T2M_MIN,ALLSKY_SFC_SW_DWN,GWETROOT,GWETTOP,RH2M,WS2M"
POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

# How many years of history to pull for a location's climatology / anomalies.
POWER_HISTORY_YEARS = 20

# app/ml/data.py -> app/ml -> app -> app/data/cache
DEFAULT_CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"

# Pilot coordinates across the Central American Dry Corridor.
PILOT_SITES = [
    {"location": "GT", "name": "Guatemala (Dry Corridor)", "latitude": 14.8, "longitude": -90.5},
    {"location": "NI", "name": "Nicaragua (Dry Corridor)", "latitude": 13.2, "longitude": -86.1},
    {"location": "HN", "name": "Honduras (Dry Corridor)", "latitude": 15.1, "longitude": -87.9},
]

# A climate-diverse global set the model trains on, so the IsolationForest and
# calibration see normal/anomalous combinations from many climates — not just
# the tropics. Includes Mediterranean and Southern-hemisphere points.
GLOBAL_SITES = PILOT_SITES + [
    {"location": "IT", "name": "Florence, Italy (Mediterranean)", "latitude": 43.77, "longitude": 11.26},
    {"location": "ES", "name": "Spain Meseta (Mediterranean)", "latitude": 40.4, "longitude": -4.0},
    {"location": "SN", "name": "Senegal (Sahel)", "latitude": 14.7, "longitude": -16.5},
    {"location": "IN", "name": "Deccan, India (monsoon)", "latitude": 17.4, "longitude": 78.5},
    {"location": "US", "name": "US Great Plains", "latitude": 39.0, "longitude": -99.0},
    {"location": "KE", "name": "Kenya (equatorial)", "latitude": 0.5, "longitude": 37.5},
    {"location": "BR", "name": "Cerrado, Brazil (S. hemisphere)", "latitude": -15.6, "longitude": -47.8},
    {"location": "AU", "name": "SE Australia (S. hemisphere)", "latitude": -34.5, "longitude": 146.0},
]


def history_range():
    """Stable (lat/lon-independent) POWER date range: 20 yrs through the start
    of the current month. Month-stable so the cache persists day to day."""
    today = date.today()
    start = date(today.year - POWER_HISTORY_YEARS, 1, 1)
    end = date(today.year, today.month, 1)
    return start.strftime("%Y%m%d"), end.strftime("%Y%m%d")


def cache_path(lat: float, lon: float, start: str, end: str, cache_dir: Path = DEFAULT_CACHE_DIR) -> Path:
    cache_dir = Path(cache_dir)
    return cache_dir / f"power_{lat}_{lon}_{start}_{end}.json"


def _http_get_json(url: str, params: dict) -> dict:
    """Isolated so tests can monkeypatch it; `requests` is imported lazily so
    importing this module (and thus risk.py) never pulls the network stack."""
    import requests

    resp = requests.get(url, params=params, timeout=60)
    resp.raise_for_status()
    return resp.json()


def fetch_power(
    lat: float,
    lon: float,
    start: str,
    end: str,
    cache_dir: Path = DEFAULT_CACHE_DIR,
) -> dict:
    """Return the raw POWER JSON for a point, hitting cache first.

    `start`/`end` are YYYYMMDD strings. Writes the raw response to cache so the
    next call (and the live demo) never touches the network.
    """
    path = cache_path(lat, lon, start, end, cache_dir)
    if path.exists():
        return json.loads(path.read_text())

    params = {
        "parameters": POWER_PARAMETERS,
        "latitude": lat,
        "longitude": lon,
        "start": start,
        "end": end,
        "format": "JSON",
        "community": "AG",
    }
    payload = _http_get_json(POWER_URL, params)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload))
    return payload


# --------------------------------------------------------------------------- #
# MODIS NDVI — keyless ORNL DAAC REST web service
# --------------------------------------------------------------------------- #
# 250 m, 16-day NDVI composite. Keyless point time-series, no Earthdata login.
MODIS_URL = "https://modis.ornl.gov/rst/api/v1/MOD13Q1/subset"
MODIS_BAND = "250m_16_days_NDVI"
# The ORNL REST /subset endpoint rejects ranges longer than 10 composites
# ("maximum subset tiles support of 10"), i.e. ~160 days. Chunk below that.
MODIS_MAX_DAYS = 150


def _date_chunks(start: str, end: str, max_days: int):
    s = datetime.strptime(start, "%Y%m%d")
    e = datetime.strptime(end, "%Y%m%d")
    cur = s
    while cur <= e:
        ce = min(e, cur + timedelta(days=max_days))
        yield cur.strftime("%Y%m%d"), ce.strftime("%Y%m%d")
        cur = ce + timedelta(days=1)


def _to_modis_date(yyyymmdd: str) -> str:
    """YYYYMMDD -> MODIS 'A{YYYY}{DOY:03d}' date string."""
    d = datetime.strptime(yyyymmdd, "%Y%m%d")
    return f"A{d.year}{d.timetuple().tm_yday:03d}"


def modis_cache_path(lat: float, lon: float, start: str, end: str, cache_dir: Path = DEFAULT_CACHE_DIR) -> Path:
    cache_dir = Path(cache_dir)
    return cache_dir / f"modis_{lat}_{lon}_{start}_{end}.json"


def _modis_get_json(url: str, params: dict) -> dict:
    """Isolated for tests; `requests` imported lazily so importing this module
    never pulls the network stack."""
    import requests

    resp = requests.get(url, params=params, timeout=90, headers={"Accept": "application/json"})
    resp.raise_for_status()
    return resp.json()


def fetch_modis_ndvi(
    lat: float,
    lon: float,
    start: str,
    end: str,
    cache_dir: Path = DEFAULT_CACHE_DIR,
) -> dict:
    """Return the raw MODIS NDVI subset JSON for a point, hitting cache first.

    `start`/`end` are YYYYMMDD strings. Raw NDVI values are integers scaled by
    `scale` (0.0001); fill is -3000. Parsing/masking happens downstream.
    """
    path = modis_cache_path(lat, lon, start, end, cache_dir)
    if path.exists():
        return json.loads(path.read_text())

    merged = None
    for cs, ce in _date_chunks(start, end, MODIS_MAX_DAYS):
        params = {
            "latitude": lat,
            "longitude": lon,
            "startDate": _to_modis_date(cs),
            "endDate": _to_modis_date(ce),
            "band": MODIS_BAND,
            "kmAboveBelow": 0,
            "kmLeftRight": 0,
        }
        payload = _modis_get_json(MODIS_URL, params)
        if merged is None:
            merged = payload
        else:
            merged.setdefault("subset", []).extend(payload.get("subset", []))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(merged))
    return merged
