"""Chemin « données en direct » (Flux 1) + score ML (Flux 2), sans réseau.

On remplace live_data.fetch par une réponse figée au format de live_data.summarize,
puis on vérifie que /api/recommendation : utilise le direct (data_mode "real"),
calcule le risque avec le modèle ML, et garde toutes les clés lues par le front.
"""
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

import live_data
import main

client = TestClient(main.app)
MONTHS = live_data.MONTHS


def _fake_live(rain_scale: float) -> dict:
    today = date(2026, 6, 10)
    days = [(today - timedelta(days=i)).isoformat() for i in range(60, 0, -1)]
    rain = {d: 6.0 * rain_scale for d in days}
    clim = {m: 6.0 for m in MONTHS}
    fc = [{"date": (today + timedelta(days=i)).isoformat(), "rain_mm": 8.0 * rain_scale,
           "et0_mm": 4.5, "tmax_c": 31.0} for i in range(16)]
    return {
        "today": today.isoformat(), "rain_daily": rain, "rainfall_60d_mm": round(sum(rain.values())),
        "rainfall_normal_mm": 360, "clim_mm_day": clim, "soil_moisture": 0.3 * rain_scale + 0.05,
        "ndvi": 0.6, "ndvi_trend": 0.02 if rain_scale > 0.5 else -0.12, "ndvi_points": [("2026-05-25", 0.6)],
        "et0_mm_day": 4.5, "temperature_7d_c": 27.0, "temp_anomaly": 0.5 if rain_scale > 0.5 else 2.0,
        "solar_mj_m2": 20.0, "forecast": fc, "forecast_rain_16d_mm": round(sum(f["rain_mm"] for f in fc)),
        "current": {"time": "2026-06-10T09:00", "temperature_c": 26.0, "wind_speed_kmh": 8.0,
                    "wind_dir_deg": 90, "humidity_pct": 70, "precip_mm": 0.0},
        "daily": {}, "sources": [{"name": "NASA POWER", "what": "rain", "date": "2026-06-08", "live": True}],
        "errors": {}, "fetched_at": "2026-06-10T09:00",
    }


@pytest.fixture
def live_on(monkeypatch):
    monkeypatch.setenv("FIELDSHIFT_LIVE", "1")


@pytest.mark.parametrize("lang", ["fr", "en", "it"])
def test_live_recommendation_uses_ml_and_keeps_front_shape(live_on, monkeypatch, lang):
    monkeypatch.setattr(live_data, "fetch", lambda lat, lon: _fake_live(1.0))
    d = client.post("/api/recommendation", json={"latitude": 13.3, "longitude": -87.2, "crop": "maize", "lang": lang}).json()
    assert d["live"] is True and d["data_mode"] == "real" and d["_mock"] is False
    assert d["risk_model"] == "ml" and 0 <= d["risk_score"] <= 100
    for k in ("water_budget", "planting_timeline", "rotations", "season", "weather", "forecast",
              "series", "risk_components", "week_focus", "data_sources"):
        assert k in d, k
    assert len(d["forecast"]) == 16


def test_ml_risk_is_higher_when_live_data_is_dry(live_on, monkeypatch):
    monkeypatch.setattr(live_data, "fetch", lambda lat, lon: _fake_live(1.0))
    wet = client.post("/api/recommendation", json={"latitude": 13.3, "longitude": -87.2}).json()
    monkeypatch.setattr(live_data, "fetch", lambda lat, lon: _fake_live(0.2))
    dry = client.post("/api/recommendation", json={"latitude": 13.3, "longitude": -87.2}).json()
    assert dry["risk_score"] > wet["risk_score"]
