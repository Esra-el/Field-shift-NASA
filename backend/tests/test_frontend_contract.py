"""Garde-fou d'intégration : le VRAI backend (/api/*) renvoie EXACTEMENT la forme
que la PWA du Flux 1 consomme. Chaque assertion correspond à une clé lue par un
fichier frontend/js/*.js — si l'une casse, une page du front casserait.

Hermétique : pas de clé Gemini (fallback déterministe), données réelles servies
depuis le cache NASA POWER des sites pilotes (aucun réseau).
"""
import re

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

PILOT = {  # coord pilote -> POWER en cache -> data_mode "real", hors-ligne
    "latitude": 14.8, "longitude": -90.5,
    "crop": "maize", "soil_type": "sandy_loam",
    "irrigation": False, "priority": "balanced",
}
LEVELS = {"low", "moderate", "high"}
WINDOW_RE = re.compile(r"\d{4}-\d{2}-\d{2}.*?\d{4}-\d{2}-\d{2}")  # parseWindow() du front


@pytest.fixture(autouse=True)
def _no_live_gemini(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


@pytest.mark.parametrize("lang", ["fr", "en", "it"])
def test_recommendation_matches_frontend_contract(lang):
    r = client.post("/api/recommendation", json={**PILOT, "lang": lang})
    assert r.status_code == 200
    d = r.json()

    # --- panel.js / plan.js / analyse.js / cooperativa.js : clés de tête
    assert isinstance(d["risk_score"], int) and 0 <= d["risk_score"] <= 100
    assert d["risk_level"] in LEVELS
    assert isinstance(d["ai_explanation"], str) and d["ai_explanation"]
    assert isinstance(d["_mock"], bool)
    # coord pilote en cache -> vraies données
    assert d["data_mode"] == "real" and d["_mock"] is False

    # --- water_budget (plan.js, panel.js renderWeather, cooperativa.js)
    wb = d["water_budget"]
    for k in ("status", "crop_water_need_mm", "available_water_mm", "deficit_mm", "coverage_pct", "explanation"):
        assert k in wb, f"water_budget.{k} manquant"
    assert wb["status"] in {"enough_water", "risky", "not_enough_water"}
    assert isinstance(wb["coverage_pct"], (int, float))

    # --- planting_timeline : le front attend 'switch_crop' (jamais 'switch' nu)
    pt = d["planting_timeline"]
    assert pt["recommendation"] in {"plant_now", "wait", "switch_crop"}
    assert WINDOW_RE.search(pt["best_window"]), "best_window illisible pour parseWindow()"
    assert isinstance(pt["reason"], str) and pt["reason"]

    # --- rotations (plan.js, cooperativa.js) : 3 plans typés
    rots = d["rotations"]
    assert len(rots) == 3
    assert {r["type"] for r in rots} == {"safest", "balanced", "highest_yield"}
    for rr in rots:
        assert rr["risk"] in LEVELS
        assert rr["name"] and rr["reason"]

    # --- nasa_indicators (panel.js tiles, plan.js, analyse.js)
    ind = d["nasa_indicators"]
    for k in ("rainfall_60d_mm", "rainfall_normal_mm", "soil_moisture", "ndvi_trend", "solar_radiation", "evapotranspiration"):
        assert k in ind, f"nasa_indicators.{k} manquant"

    # --- series (panel.js drawChart, plan.js drawCharts, analyse.js drawGrowth)
    s = d["series"]
    n = len(s["labels"])
    assert n == 8
    for k in ("rainfall_mm", "rainfall_normal_mm", "soil_moisture", "ndvi", "temperature_c", "solar_radiation"):
        assert k in s, f"series.{k} manquant"
        assert len(s[k]) == n, f"series.{k} doit avoir {n} points"

    # --- risk_components (plan.js 'pourquoi ce risque', analyse.js updates, topbar alerte)
    rc = d["risk_components"]
    assert {c["factor"] for c in rc} == {"rainfall", "soil_moisture", "ndvi", "heat"}
    for c in rc:
        assert c["level"] in {"ok", "warn", "bad"}
        assert c["value"] and c["source"] and c["weight"]


def test_uncached_field_degrades_to_mock_without_crashing():
    # Coord non mise en cache, sans FIELDSHIFT_ALLOW_FETCH -> synthétique, honnête.
    r = client.post("/api/recommendation", json={**PILOT, "latitude": 0.0, "longitude": 0.0})
    assert r.status_code == 200
    d = r.json()
    assert d["data_mode"] == "mock" and d["_mock"] is True
    # La forme reste complète même en repli.
    assert "series" in d and "risk_components" in d and d["planting_timeline"]["recommendation"] in {"plant_now", "wait", "switch_crop"}


@pytest.mark.parametrize("lang", ["fr", "en", "it"])
def test_copilot_matches_frontend_contract(lang):
    reco = client.post("/api/recommendation", json={**PILOT, "lang": lang}).json()
    r = client.post("/api/copilot", json={"question": "¿Tengo suficiente agua?", "context": reco, "lang": lang})
    assert r.status_code == 200
    d = r.json()
    assert isinstance(d["answer"], str) and d["answer"]      # copiloto.js: res.answer
    assert isinstance(d["sources"], list)                     # copiloto.js: res.sources


def test_backtesting_matches_frontend_contract():
    r = client.post("/api/backtesting", json={**PILOT, "lang": "fr"})
    assert r.status_code == 200
    d = r.json()
    assert isinstance(d["summary"], str) and d["summary"]     # backtesting.js: data.summary
    assert isinstance(d["seasons"], list) and d["seasons"]
    for s in d["seasons"]:                                    # backtesting.js render()
        for k in ("season", "tag", "rainfall_pct", "risk_score", "risk_level", "outcome", "warned"):
            assert k in s, f"season.{k} manquant"
        assert s["risk_level"] in LEVELS
