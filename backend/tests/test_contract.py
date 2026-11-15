"""Contract tests — guarantee /recommend always returns the §8.6 shape.

If one of these fails after a change, the frontend would break. Keep them green.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _force_copilot_fallback(monkeypatch):
    """Keep these tests hermetic: never a live Gemini call, regardless of a key in .env."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

SAMPLE = {
    "latitude": 14.8,
    "longitude": -90.5,
    "crop": "maize",
    "soil_type": "sandy_loam",
    "irrigation": False,
    "priority": "save_water",
}


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_recommend_returns_full_contract():
    r = client.post("/recommend", json=SAMPLE)
    assert r.status_code == 200
    data = r.json()

    for key in [
        "risk_score",
        "risk_level",
        "water_budget",
        "planting_timeline",
        "rotations",
        "nasa_indicators",
        "ai_explanation",
    ]:
        assert key in data, f"missing top-level key: {key}"

    assert 0 <= data["risk_score"] <= 100
    assert data["risk_level"] in ["low", "moderate", "high"]

    wb = data["water_budget"]
    for k in ["status", "crop_water_need_mm", "available_water_mm", "deficit_mm", "explanation"]:
        assert k in wb
    assert wb["status"] in ["enough_water", "risky", "not_enough_water"]

    pt = data["planting_timeline"]
    assert pt["recommendation"] in ["plant_now", "wait", "switch"]

    assert len(data["rotations"]) == 3
    assert {rot["type"] for rot in data["rotations"]} == {"safest", "balanced", "highest_yield"}

    ind = data["nasa_indicators"]
    for k in [
        "rainfall_60d_mm",
        "rainfall_normal_mm",
        "soil_moisture",
        "ndvi_trend",
        "solar_radiation",
        "evapotranspiration",
    ]:
        assert k in ind


def test_deterministic():
    """Same field -> same result (stable live demo)."""
    a = client.post("/recommend", json=SAMPLE).json()
    b = client.post("/recommend", json=SAMPLE).json()
    assert a["risk_score"] == b["risk_score"]


def test_irrigation_improves_water_budget():
    """Architecture invariant: irrigation helps the WATER BUDGET, not the drought risk.

    Drought risk is a property of the climate/soil and can't be changed by irrigation;
    irrigation adds available water, so the deficit must not increase.
    """
    dry = client.post("/recommend", json={**SAMPLE, "irrigation": False}).json()
    wet = client.post("/recommend", json={**SAMPLE, "irrigation": True}).json()
    assert wet["water_budget"]["deficit_mm"] <= dry["water_budget"]["deficit_mm"]
    assert wet["risk_score"] == dry["risk_score"]  # climate-only, unchanged by irrigation
