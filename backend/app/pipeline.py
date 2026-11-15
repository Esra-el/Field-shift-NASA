"""The pipeline — the MERGE POINT where everyone's work comes together. (main owns this.)

Flow (this is the whole system in one place):

    indicators  ->  ml.predict_risk     -> risk score      (the `ml` agent's module)
                ->  water_budget engine  -> water status    (deterministic rules)
                ->  planting engine      -> plant/wait/switch
                ->  rotation engine       -> 3 ranked plans
                ->  copilot.explain      -> plain-language explanation (the `ai` agent's module)
                ->  Recommendation (the §8.6 contract)

The two agent modules plug in through `predict_risk()` and `copilot.explain()/answer()`.
Nothing here needs to change when they swap their stubs for the real thing.
"""
from __future__ import annotations

from .schemas import FieldRequest, Recommendation, NasaIndicators, RiskLevel
from .data.indicators import get_indicators, risk_features_z
from .ml.risk import predict_risk
from .engines.water_budget import compute_water_budget
from .engines.planting import compute_planting
from .engines.rotation import rank_rotations
from . import copilot


def build_recommendation(req: FieldRequest, lang: str = "es") -> Recommendation:
    indicators = get_indicators(req)

    # 1) ml agent's module — drought risk as z-scores vs this location's own
    #    history (global SPI model; irrigation-independent)
    risk = predict_risk(risk_features_z(req, indicators))
    risk_level = RiskLevel(risk["risk_level"])

    # 2) deterministic rule engines
    water_budget = compute_water_budget(indicators, req.crop, req.irrigation)
    planting = compute_planting(water_budget.status, risk_level)
    rotations = rank_rotations(req.priority)

    nasa = NasaIndicators(
        rainfall_60d_mm=indicators["rainfall_60d_mm"],
        rainfall_normal_mm=indicators["rainfall_normal_mm"],
        soil_moisture=indicators["soil_moisture"],
        ndvi_trend=indicators["ndvi_trend"],
        solar_radiation=indicators["solar_radiation"],
        evapotranspiration=indicators["evapotranspiration"],
    )

    data_mode = "real" if indicators.get("source") == "power" else "mock"

    rec = Recommendation(
        risk_score=int(risk["risk_score"]),
        risk_level=risk_level,
        water_budget=water_budget,
        planting_timeline=planting,
        rotations=rotations,
        nasa_indicators=nasa,
        ai_explanation="",  # filled next by the ai agent's module
        data_mode=data_mode,
    )

    # 3) ai agent's module — explain the finished recommendation (never alters the numbers)
    rec.ai_explanation = copilot.explain(
        rec.model_dump(mode="json"), req.model_dump(mode="json"), lang=lang
    )
    return rec


def answer_question(question: str, req: FieldRequest, lang: str = "es") -> str:
    rec = build_recommendation(req, lang=lang)
    return copilot.answer(
        question, rec.model_dump(mode="json"), req.model_dump(mode="json"), lang=lang
    )
