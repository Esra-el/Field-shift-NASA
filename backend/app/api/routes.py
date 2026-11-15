"""API routes.

    GET  /health     liveness
    POST /recommend  the full planting recommendation (the §8.6 contract)
    POST /ask        ask the copilot a question about a field
"""
from fastapi import APIRouter
from pydantic import BaseModel

from ..schemas import FieldRequest, Recommendation
from ..pipeline import build_recommendation, answer_question
from .. import copilot

router = APIRouter()


@router.get("/health", tags=["meta"])
def health():
    # `copilot` reports non-secret status (model, whether a key is set and
    # looks valid, last failure reason) so the live copilot can be diagnosed
    # without server logs. It never exposes the API key.
    return {"status": "ok", "copilot": copilot.status()}


@router.post("/recommend", response_model=Recommendation, tags=["recommendation"])
def recommend(req: FieldRequest) -> Recommendation:
    """Full planting recommendation for one field: risk, water budget, timeline, rotations."""
    return build_recommendation(req)


class AskRequest(BaseModel):
    question: str
    field: FieldRequest
    lang: str = "es"


@router.post("/ask", tags=["copilot"])
def ask(body: AskRequest):
    """Ask the explainable copilot a question, grounded in this field's recommendation."""
    return {"answer": answer_question(body.question, body.field, lang=body.lang)}
