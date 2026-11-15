"""The Field Shift API contract — the single source of truth both sides agree on.

These Pydantic models ARE the §8.6 contract from the Team Workflow doc. The
frontend builds against this shape; the backend fills it in. When the real
engines replace the mock, nothing here changes, so the frontend never breaks.
"""
from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Controlled vocabularies (keep the frontend and backend from drifting)
# --------------------------------------------------------------------------- #
class Priority(str, Enum):
    save_water = "save_water"
    max_yield = "max_yield"
    soil_health = "soil_health"
    balanced = "balanced"


class RiskLevel(str, Enum):
    low = "low"
    moderate = "moderate"
    high = "high"


class WaterStatus(str, Enum):
    enough_water = "enough_water"
    risky = "risky"
    not_enough_water = "not_enough_water"


class PlantingAction(str, Enum):
    plant_now = "plant_now"
    wait = "wait"
    switch = "switch"


class RotationType(str, Enum):
    safest = "safest"
    balanced = "balanced"
    highest_yield = "highest_yield"


class Level(str, Enum):
    low = "low"
    moderate = "moderate"
    high = "high"


# --------------------------------------------------------------------------- #
# Request
# --------------------------------------------------------------------------- #
class FieldRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, examples=[14.8])
    longitude: float = Field(..., ge=-180, le=180, examples=[-90.5])
    crop: str = Field(..., examples=["maize"])
    soil_type: str = Field("unknown", examples=["sandy_loam"])
    irrigation: bool = Field(False)
    priority: Priority = Field(Priority.balanced, examples=["save_water"])


# --------------------------------------------------------------------------- #
# Response pieces
# --------------------------------------------------------------------------- #
class WaterBudget(BaseModel):
    status: WaterStatus
    crop_water_need_mm: float
    available_water_mm: float
    deficit_mm: float
    explanation: str


class PlantingTimeline(BaseModel):
    recommendation: PlantingAction
    best_window: str = Field(..., examples=["2026-11-20 to 2026-11-30"])
    reason: str


class Rotation(BaseModel):
    type: RotationType
    name: str = Field(..., examples=["Beans → Sorghum → Cover crop"])
    water_saving: Level
    soil_benefit: Level
    risk: Level
    reason: str


class NasaIndicators(BaseModel):
    rainfall_60d_mm: float
    rainfall_normal_mm: float
    soil_moisture: float
    ndvi_trend: float
    solar_radiation: float
    evapotranspiration: float


class Recommendation(BaseModel):
    risk_score: int = Field(..., ge=0, le=100)
    risk_level: RiskLevel
    water_budget: WaterBudget
    planting_timeline: PlantingTimeline
    rotations: List[Rotation]
    nasa_indicators: NasaIndicators
    ai_explanation: str
    # Honesty flag the UI (and judges) can see: "mock" until real NASA data is wired in.
    data_mode: str = Field("mock")
