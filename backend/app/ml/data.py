"""NASA POWER data access — OWNED BY THE `ml` AGENT.

The ONLY module that touches the network, and only at train time. Every raw
response is cached to app/data/cache/ so the model can be rebuilt — and the
demo can run — with no live API dependency.

NASA POWER daily point API (no auth):
  https://power.larc.nasa.gov/api/temporal/daily/point
"""
from __future__ import annotations

import json
from pathlib import Path

# Daily variables we pull. PRECTOTCORR (rain), T2M/MAX/MIN (temperature),
# ALLSKY_SFC_SW_DWN (solar), RH2M/WS2M kept for future water-balance work.
POWER_PARAMETERS = "PRECTOTCORR,T2M,T2M_MAX,T2M_MIN,ALLSKY_SFC_SW_DWN,RH2M,WS2M"
POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

# app/ml/data.py -> app/ml -> app -> app/data/cache
DEFAULT_CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"

# Pilot coordinates across the Central American Dry Corridor.
PILOT_SITES = [
    {"location": "GT", "name": "Guatemala (Dry Corridor)", "latitude": 14.8, "longitude": -90.5},
    {"location": "NI", "name": "Nicaragua (Dry Corridor)", "latitude": 13.2, "longitude": -86.1},
    {"location": "HN", "name": "Honduras (Dry Corridor)", "latitude": 15.1, "longitude": -87.9},
]


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
