"""Planting-timeline engine (deterministic). main owns this.

Reconciles the two signals — drought risk (from ml) and the water budget — into
a single action a farmer can act on: plant now, wait, or switch crop/rotation.
"""
from __future__ import annotations

from datetime import date, timedelta

from ..schemas import PlantingTimeline, PlantingAction, WaterStatus, RiskLevel


def compute_planting(status: WaterStatus, risk_level: RiskLevel) -> PlantingTimeline:
    today = date.today()

    if status == WaterStatus.not_enough_water:
        action = PlantingAction.switch     # the crop can't be supplied -> change crop/rotation
    elif status == WaterStatus.risky or risk_level == RiskLevel.high:
        action = PlantingAction.wait       # borderline water or HIGH drought risk -> wait
    else:
        action = PlantingAction.plant_now

    if action == PlantingAction.plant_now:
        start, end = today, today + timedelta(days=10)
        reason = "Soil moisture and expected rainfall are sufficient for the early growth stages."
    elif action == PlantingAction.wait:
        start, end = today + timedelta(days=7), today + timedelta(days=17)
        reason = "Soil moisture is low; waiting for the next rains lowers the risk of early-season water stress."
    else:  # switch
        start, end = today + timedelta(days=7), today + timedelta(days=21)
        reason = "The water deficit is too large for this crop; a more drought-tolerant rotation is safer this season."

    return PlantingTimeline(
        recommendation=action,
        best_window=f"{start.isoformat()} to {end.isoformat()}",
        reason=reason,
    )
