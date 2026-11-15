"""Field Shift — Application FastAPI.

Flux 1 (Zlat) : la PWA + les données en direct.  Flux 2 (Esra) : le vrai moteur ML/IA.

Ce fichier sert la PWA (fichiers statiques du front) et expose l'API au format
du contrat §8.6 :

  * /api/recommendation : données EN DIRECT (live_data : NASA POWER, Open-Meteo,
    NASA MODIS) -> moteur complet (mock_engine en mode « live ») dont le score de
    risque vient du MODÈLE ML du Flux 2 (app/ml). Si le direct ne répond pas, on
    passe par `real_engine` (NASA POWER en cache des sites pilotes, sinon mock).
  * /api/backtesting : vrai backtesting ML du Flux 2 (`real_engine`).
  * /api/copilot : copilote Gemini du Flux 2 (`real_engine`), fallback local.

Exécuter :
    cd backend
    pip install -r requirements.txt
    uvicorn main:app --reload
Puis ouvrir : http://127.0.0.1:8000/
(Pour le copilote IA en direct : mettre GEMINI_API_KEY dans backend/.env —
sans clé, les réponses restent utiles via le fallback déterministe.)
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Charge backend/.env (clé Gemini) si présent — no-op sinon.
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent / ".env")
except Exception:
    pass

import live_data
import mock_engine

try:  # vrai moteur du Flux 2 (ML + Gemini). S'il manque une dépendance, on reste sur le moteur live.
    import real_engine as engine
except Exception:  # pragma: no cover
    engine = None

FRONTEND_DIR = (Path(__file__).resolve().parent.parent / "frontend")

app = FastAPI(
    title="Field Shift API",
    description="Décisions de semis face à la sécheresse à partir des données NASA (direct + ML + IA).",
    version="1.1.0",
)

# CORS ouvert en développement (front et back peuvent tourner séparément).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Champs que le moteur du Flux 2 calcule sur données réelles (sites pilotes en cache).
_REAL_KEYS = ("risk_score", "risk_level", "water_budget", "planting_timeline",
              "nasa_indicators", "risk_components", "series", "ai_explanation")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "field-shift", "mode": "live+ml" if engine else "live"}


@app.post("/api/recommendation")
async def recommendation(payload: dict) -> JSONResponse:
    """Recommandation complète pour un champ (contrat §8.6)."""
    payload = payload or {}
    live: dict = {}
    # FIELDSHIFT_LIVE=0 coupe le direct (tests hermétiques, démo hors ligne).
    live_on = os.environ.get("FIELDSHIFT_LIVE", "1").lower() not in ("0", "false", "no")
    if live_on and payload.get("live", True):
        try:
            lat = float(payload.get("latitude", 14.8))
            lon = float(payload.get("longitude", -90.5))
            # NASA POWER + Open-Meteo + MODIS en direct (en parallèle, ~1-12 s, cache 1 h)
            live = await run_in_threadpool(live_data.fetch, lat, lon)
        except (TypeError, ValueError):
            live = {}
    result = mock_engine.generate_recommendation(payload, live)

    # Pas de direct (hors ligne, API en panne) : on garde la forme complète attendue
    # par le front, mais on prend les nombres réels du moteur Flux 2 s'il en a.
    if not result.get("live") and engine is not None:
        try:
            real = await run_in_threadpool(engine.generate_recommendation, payload)
            if real.get("data_mode") == "real":
                for k in _REAL_KEYS:
                    if k in real:
                        result[k] = real[k]
                result["data_mode"] = "real"
                result["_mock"] = False
        except Exception:
            pass
    return JSONResponse(result)


@app.post("/api/backtesting")
async def backtest(payload: dict) -> JSONResponse:
    """Backtesting : « l'outil aurait-il prévenu ? » sur les saisons sèches passées."""
    payload = payload or {}
    fn = engine.backtesting if engine is not None else mock_engine.backtesting
    return JSONResponse(await run_in_threadpool(fn, payload))


@app.post("/api/copilot")
async def copilot(payload: dict) -> JSONResponse:
    """Copilote IA (Gemini). Entrée : {question, context, lang}."""
    payload = payload or {}
    fn = engine.copilot_answer if engine is not None else mock_engine.copilot_answer
    return JSONResponse(await run_in_threadpool(
        fn,
        question=str(payload.get("question", "")),
        context=payload.get("context"),
        lang=str(payload.get("lang", "fr")),
    ))


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    """La racine ouvre le site public (site.html). L'application commence à /inicio.html."""
    return FileResponse(FRONTEND_DIR / "site.html")


# IMPORTANT : monter les statiques en dernier, pour ne pas masquer les routes /api.
if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
