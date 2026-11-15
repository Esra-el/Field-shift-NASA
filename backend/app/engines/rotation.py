"""Crop-rotation engine (rules + priority ranking). main owns this.

Always returns the same three plans (safest / balanced / highest-yield), ordered
so the plan matching the farmer's stated priority comes first. A later ML-assisted
ranker can reorder within this, but the three options stay transparent.
"""
from __future__ import annotations

from typing import List

from ..schemas import Rotation, RotationType, Level, Priority


def rank_rotations(priority: Priority) -> List[Rotation]:
    base = {
        RotationType.safest: Rotation(
            type=RotationType.safest,
            name="Beans → Sorghum → Cover crop (mucuna)",
            water_saving=Level.high,
            soil_benefit=Level.high,
            risk=Level.low,
            reason="Low water dependence and continuous soil cover reduce drought exposure.",
        ),
        RotationType.balanced: Rotation(
            type=RotationType.balanced,
            name="Cowpea → Maize → Cover / fallow",
            water_saving=Level.moderate,
            soil_benefit=Level.high,
            risk=Level.moderate,
            reason="Keeps a cereal harvest while a legume and fallow restore soil nitrogen and moisture.",
        ),
        RotationType.highest_yield: Rotation(
            type=RotationType.highest_yield,
            name="Maize → Maize (with water-risk alerts)",
            water_saving=Level.low,
            soil_benefit=Level.low,
            risk=Level.high,
            reason="Highest potential yield, but only safe when the water budget is comfortable.",
        ),
    }
    order = {
        Priority.save_water: [RotationType.safest, RotationType.balanced, RotationType.highest_yield],
        Priority.soil_health: [RotationType.safest, RotationType.balanced, RotationType.highest_yield],
        Priority.balanced: [RotationType.balanced, RotationType.safest, RotationType.highest_yield],
        Priority.max_yield: [RotationType.highest_yield, RotationType.balanced, RotationType.safest],
    }[priority]
    return [base[t] for t in order]
