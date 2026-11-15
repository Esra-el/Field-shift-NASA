"""Water-budget engine (deterministic agronomy). main owns this.

The core decision feature: does available water cover this crop's need?
This is where irrigation matters — it adds to available water.

    available = recent rainfall + expected rainfall + soil-moisture contribution + irrigation
    need      = crop seasonal water requirement
"""
from __future__ import annotations

from ..schemas import WaterBudget, WaterStatus

# Rough seasonal crop water needs (mm). Placeholder agronomy — refine with FAO-56 Kc later.
CROP_WATER_NEED_MM = {
    "maize": 520,
    "beans": 380,
    "sorghum": 450,
    "millet": 400,
    "cowpea": 360,
    "mucuna": 350,
}
DEFAULT_CROP_NEED = 450


def compute_water_budget(indicators: dict, crop: str, irrigation: bool) -> WaterBudget:
    need = float(CROP_WATER_NEED_MM.get(crop.lower(), DEFAULT_CROP_NEED))

    rainfall_60d = indicators["rainfall_60d_mm"]
    soil_moisture = indicators["soil_moisture"]

    expected_rain = rainfall_60d * 0.6        # crude near-term outlook
    soil_contribution = soil_moisture * 300.0  # root-zone contribution, mm
    irrigation_mm = 150.0 if irrigation else 0.0

    available = round(rainfall_60d + expected_rain + soil_contribution + irrigation_mm, 0)
    deficit = round(need - available, 0)

    if deficit <= 0:
        status = WaterStatus.enough_water
    elif deficit <= need * 0.30:
        status = WaterStatus.risky               # 0-30% short: borderline
    else:
        status = WaterStatus.not_enough_water    # >30% short: this crop likely won't make it

    coverage_pct = round(available / need * 100)
    return WaterBudget(
        status=status,
        crop_water_need_mm=need,
        available_water_mm=available,
        deficit_mm=deficit,
        explanation=f"Estimated rainfall and soil moisture cover about {coverage_pct}% of this crop's water need.",
    )
