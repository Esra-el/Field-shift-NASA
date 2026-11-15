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


def test_cold_season_blocks_planting_even_when_wet(live_on, monkeypatch):
    # Hiver tempéré (ex. Florence) : humide MAIS trop froid -> « attendre », pas « semer ».
    cold = _fake_live(1.0)
    cold["temperature_7d_c"] = 8.0
    cold["temp_normal_monthly"] = {m: t for m, t in zip(
        MONTHS, [6, 7, 10, 13, 17, 22, 25, 25, 21, 16, 10, 7])}  # climat tempéré
    cold["today"] = "2026-11-15"  # novembre : entrée en hiver
    monkeypatch.setattr(live_data, "fetch", lambda lat, lon: cold)
    d = client.post("/api/recommendation", json={"latitude": 43.77, "longitude": 11.26, "crop": "maize"}).json()
    pt = d["planting_timeline"]
    assert pt["recommendation"] == "wait", pt
    assert pt["basis"] == "cold", pt
    # La fenêtre conseillée tombe au printemps (mois chaud), pas en plein hiver.
    assert pt["best_window"][5:7] in {"04", "05", "06"}, pt["best_window"]


def test_warm_tropics_never_triggers_cold_gate(live_on, monkeypatch):
    warm = _fake_live(0.2)  # sec
    warm["temperature_7d_c"] = 28.0
    warm["temp_normal_monthly"] = {m: 26.0 for m in MONTHS}  # toujours chaud
    monkeypatch.setattr(live_data, "fetch", lambda lat, lon: warm)
    d = client.post("/api/recommendation", json={"latitude": 13.3, "longitude": -87.2, "crop": "maize"}).json()
    assert d["planting_timeline"]["basis"] != "cold"


def test_ml_risk_is_higher_when_live_data_is_dry(live_on, monkeypatch):
    monkeypatch.setattr(live_data, "fetch", lambda lat, lon: _fake_live(1.0))
    wet = client.post("/api/recommendation", json={"latitude": 13.3, "longitude": -87.2}).json()
    monkeypatch.setattr(live_data, "fetch", lambda lat, lon: _fake_live(0.2))
    dry = client.post("/api/recommendation", json={"latitude": 13.3, "longitude": -87.2}).json()
    assert dry["risk_score"] > wet["risk_score"]


# --- Pluie 60 j et normale : toujours de la même famille de sources ---------------
def _raw(today: date, with_era5: bool, with_meteo: bool = True) -> dict:
    past = [(today - timedelta(days=i)).isoformat() for i in range(70, -1, -1)]
    raw = {
        "power": {"PRECTOTCORR": {d: 10.0 for d in past[:-3]}},  # POWER : 2x plus de pluie
        "clim": {**{m: 10.0 for m in MONTHS}, "_T2M": {}},
    }
    if with_meteo:
        raw["meteo"] = {"current": {"time": today.isoformat() + "T12:00"},
                        "daily": {"time": past, "precipitation_sum": [5.0] * len(past)}}
    if with_era5:
        raw["era5"] = {"doy": {f"{m:02d}-{d:02d}": 4.0 for m in range(1, 13) for d in range(1, 32)},
                       "monthly": {m: 4.0 for m in MONTHS}}
    return raw


def test_rain_open_meteo_paired_with_era5_normal():
    out = live_data.summarize(_raw(date(2026, 11, 15), with_era5=True), date(2026, 11, 15))
    assert out["rain_source"] == "Open-Meteo" and out["normal_source"].startswith("ERA5")
    assert out["rainfall_60d_mm"] == 300 and out["rainfall_normal_mm"] == 240
    assert out["clim_mm_day"]["NOV"] == 4.0


def test_rain_falls_back_to_power_pair_without_era5():
    out = live_data.summarize(_raw(date(2026, 11, 15), with_era5=False), date(2026, 11, 15))
    assert out["rain_source"] == "NASA POWER" and out["normal_source"].startswith("NASA POWER")
    assert out["rainfall_normal_mm"] == 600


def test_grid_endpoint_rejects_bad_coords():
    assert client.post("/api/grid", json={"latitude": "x"}).status_code == 422
    assert client.post("/api/grid", json={"latitude": 95, "longitude": 0}).status_code == 422


def test_rotations_include_current_and_evidence(live_on):
    r = client.post("/api/recommendation", json={"latitude": 14.8, "longitude": -90.5, "crop": "maize",
                                                  "lang": "fr", "current_rotation": "maïs → maïs"}).json()
    rots = r["rotations"]
    assert len(rots) == 4 and rots[-1]["type"] == "current" and "maïs → maïs" in rots[-1]["name"]
    for ro in rots:
        assert ro["evidence"] and ro["gaps"] and ro["local_review"]


def test_ecostress_endpoint_rejects_bad_coords():
    assert client.post("/api/ecostress", json={"latitude": "x"}).status_code == 422


def test_ecostress_utm_roundtrip():
    import ecostress
    e, n = ecostress.latlon_to_utm(41.9028, 12.4964, 33)
    lat, lon = ecostress.utm_to_latlon(e, n, 33)
    assert abs(lat - 41.9028) < 1e-5 and abs(lon - 12.4964) < 1e-5
    assert ecostress.jet_value((0, 0, 0)) is None and ecostress.jet_value(ecostress._jet(0.9)) > 0.85


def test_rotations_fill_bare_periods_with_cover():
    import rotations
    from datetime import date
    today = date(2026, 11, 15)
    clim = {m: 4.0 for m in MONTHS}                 # pluie toute l'année
    tn = {m: t for m, t in zip(MONTHS, [8, 9, 12, 15, 19, 23, 26, 26, 22, 17, 12, 9])}  # climat méditerranéen
    live = {"clim_mm_day": clim, "temp_normal_monthly": tn, "forecast": [], "slope_pct": 2.0}
    plans = rotations.build(live, today, today, "maize", "", 0.3, 1.0, 0, "fr", "moderate")
    for p in plans[:3]:
        assert p["bare_days"] <= 60, (p["name"], p["bare_days"])
        assert any(c in ("mucuna", "vetch_oats") for c in p["crops"])
