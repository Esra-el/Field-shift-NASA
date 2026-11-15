"""Field indicators that feed the risk model and the water budget. (main owns this.)

Real path: reuse the `ml` agent's own NASA POWER fetch + feature engineering
(`app.ml.data` / `app.ml.features`) so the live request is scaled EXACTLY like
the data the model was trained on. For a pilot coordinate the raw POWER response
is already cached (app/data/cache/), so this is instant and offline.

Fallback path: deterministic synthetic indicators derived from the location, so
the demo never breaks for an uncached field or if anything goes wrong.

These are the INPUTS to `ml.predict_risk` and the water-budget engine — they are
*measurements*, not decisions. The risk score is computed from them downstream.

Honesty note: rainfall / temperature / solar / ET come straight from NASA POWER.
soil_moisture and NDVI are not in POWER, so in the real path they are the model's
documented climate PROXIES (real sources would be SMAP + MODIS/VIIRS).
"""
from __future__ import annotations

import hashlib
import os

from ..schemas import FieldRequest
from ..ml import data as power_data
from ..ml import features as power_features

# The NASA POWER window already cached for the pilot sites.
REAL_START, REAL_END = "20040101", "20241231"

# A growing season (~6 months) mapped onto the ~60-day planting-window scale the
# water-budget engine is calibrated for: seasonal total / 3 ≈ a representative
# 60-day figure. Keeps real data on the same scale as the synthetic fallback.
_SEASON_TO_60D = 3.0

# Only touch the network for an UNcached field when explicitly allowed.
_ALLOW_FETCH = os.environ.get("FIELDSHIFT_ALLOW_FETCH", "").lower() in ("1", "true", "yes")


def get_indicators(req: FieldRequest) -> dict:
    """Real NASA-POWER indicators when available, else a synthetic stand-in."""
    try:
        real = _power_indicators(req)
        if real is not None:
            return real
    except Exception:
        pass  # any parse/network/data problem -> safe synthetic fallback
    return _synthetic_indicators(req)


def _power_indicators(req: FieldRequest):
    lat, lon = req.latitude, req.longitude
    cached = power_data.cache_path(lat, lon, REAL_START, REAL_END).exists()
    if not cached and not _ALLOW_FETCH:
        return None  # don't hit the network implicitly; caller falls back to synthetic

    payload = power_data.fetch_power(lat, lon, REAL_START, REAL_END)  # cache-first
    matrix = power_features.build_feature_matrix(payload, lat, f"{lat},{lon}")
    if matrix is None or matrix.empty:
        return None

    row = matrix.iloc[-1]  # most recent season with complete data
    rain_clim = float(matrix["seasonal_rainfall_mm"].mean())

    return {
        "rainfall_60d_mm": round(float(row["seasonal_rainfall_mm"]) / _SEASON_TO_60D, 1),
        "rainfall_normal_mm": round(rain_clim / _SEASON_TO_60D, 1),
        "soil_moisture": round(float(row["soil_moisture"]), 2),     # POWER proxy (SMAP in prod)
        "ndvi_trend": round(float(row["ndvi_trend"]), 2),           # POWER proxy (MODIS in prod)
        "solar_radiation": round(float(row["solar_radiation"]), 1),  # real POWER
        "evapotranspiration": round(float(row["et"]), 1),           # real POWER (Hargreaves)
        "temp_anomaly": round(float(row["temp_anomaly"]), 1),       # real POWER
        "rainfall_anomaly": round(float(row["rainfall_anomaly"]), 2),  # real POWER
        "season_year": int(row["year"]),
        "source": "power",
    }


# --------------------------------------------------------------------------- #
# Synthetic fallback (offline-safe; used for uncached fields or on any error)
# --------------------------------------------------------------------------- #
def _seed(req: FieldRequest) -> int:
    key = f"{round(req.latitude, 2)}|{round(req.longitude, 2)}|{req.crop.lower()}|{req.soil_type.lower()}"
    return int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)


def _synthetic_indicators(req: FieldRequest) -> dict:
    seed = _seed(req)
    dryness = seed % 101  # latent 0..100 "how dry is this place/season" — NOT the risk score

    rainfall_normal = 210.0
    rainfall_60d = round(rainfall_normal * (1 - dryness / 150.0), 1)
    soil_moisture = round(max(0.08, 0.35 - dryness / 400.0), 2)
    ndvi_trend = round(0.02 - (dryness / 100.0) * 0.20, 2)
    solar_radiation = round(18.0 + (seed % 70) / 10.0, 1)
    evapotranspiration = round(3.5 + (dryness / 100.0) * 2.5, 1)
    temp_anomaly = round((dryness - 50) / 25.0, 1)
    rainfall_anomaly = round((rainfall_60d - rainfall_normal) / rainfall_normal, 2)

    return {
        "rainfall_60d_mm": rainfall_60d,
        "rainfall_normal_mm": rainfall_normal,
        "soil_moisture": soil_moisture,
        "ndvi_trend": ndvi_trend,
        "solar_radiation": solar_radiation,
        "evapotranspiration": evapotranspiration,
        "temp_anomaly": temp_anomaly,
        "rainfall_anomaly": rainfall_anomaly,
        "source": "synthetic",
    }


def risk_features(indicators: dict) -> dict:
    """Slice the indicators down to exactly what `ml.predict_risk` expects."""
    return {
        "rainfall_anomaly": indicators["rainfall_anomaly"],
        "soil_moisture": indicators["soil_moisture"],
        "ndvi_trend": indicators["ndvi_trend"],
        "et": indicators["evapotranspiration"],
        "temp_anomaly": indicators["temp_anomaly"],
        "solar_radiation": indicators["solar_radiation"],
    }
