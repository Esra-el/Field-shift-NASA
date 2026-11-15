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

import auth
import live_data
import mock_engine

try:  # vrai moteur du Flux 2 (ML + Gemini). S'il manque une dépendance, on reste sur le moteur live.
    import real_engine as engine
except Exception:  # pragma: no cover
    engine = None

try:  # risque par ANALOGUE 20 ans (NASA POWER, même date civile) — couvre toute la planète.
    from app.ml import analog
except Exception:  # pragma: no cover
    analog = None

try:  # copilote Gemini LÉGER (app.copilot = google-genai seul) : actif même sans le stack ML.
    from app import copilot as light_copilot
except Exception:  # pragma: no cover
    light_copilot = None


def _light_copilot_answer(question, context, lang="fr"):
    """Copilote Gemini sans dépendre du moteur ML lourd (absent sur Vercel).
    Même sortie que real_engine.copilot_answer ; repli local si pas de clé/erreur."""
    try:
        if light_copilot is not None and light_copilot._api_key():
            txt = light_copilot.answer(str(question or ""), context or {}, {}, lang=str(lang))
            if txt and txt.strip():
                return {"answer": txt.strip(),
                        "sources": ["GPM IMERG", "SMAP", "MODIS/VIIRS", "NASA POWER"],
                        "limitations": ""}
    except Exception:
        pass
    return mock_engine.copilot_answer(question=str(question or ""), context=context, lang=str(lang))

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

# Comptes utilisateurs : /api/auth/register, /login, /me
app.include_router(auth.router)

# Champs que le moteur du Flux 2 calcule sur données réelles (sites pilotes en cache).
_REAL_KEYS = ("risk_score", "risk_level", "water_budget", "planting_timeline",
              "nasa_indicators", "risk_components", "series", "ai_explanation")


@app.get("/api/health")
def health() -> dict:
    info = {"status": "ok", "service": "field-shift", "mode": "live+ml" if engine else "live"}
    # Non-secret copilot diagnostics (model, whether a key is set and LOOKS valid,
    # last failure reason) so the live Gemini copilot can be checked from the
    # browser without server logs. Never exposes the API key.
    try:
        from app import copilot
        info["copilot"] = copilot.status()
    except Exception as exc:  # pragma: no cover - never let health hard-fail
        info["copilot"] = {"available": False, "error": type(exc).__name__}
    return info


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

    # Score de risque par ANALOGUE sur 20 ans de NASA POWER à la MÊME date civile :
    # on compare les conditions récentes à chaque 15/11 (±10 j) des 20 dernières années
    # pour ce point précis. Source NASA unique, globale. Ne bloque jamais la réponse.
    analog_on = os.environ.get("FIELDSHIFT_ANALOG", "1").lower() not in ("0", "false", "no")
    if analog is not None and analog_on and payload.get("live", True):
        try:
            a_lat = float(payload.get("latitude", 14.8))
            a_lon = float(payload.get("longitude", -90.5))
            ana = await run_in_threadpool(analog.analog, a_lat, a_lon)
            if ana.get("source") == "power_analog":
                # The analog is shown as a labeled 20-year NASA insight — we do NOT
                # override the final risk number (the water-budget engine computes it
                # and the explanation text quotes it; overriding only the number made
                # the dashboard contradict itself). Coherence first.
                result["analog"] = ana          # percentile + drivers (20 ans NASA POWER)
                head = analog.headline(ana, str(payload.get("lang", "fr")))
                if head:  # visible at the top of #ai-explain, no front-end change needed
                    result["ai_explanation"] = (head + " " + (result.get("ai_explanation") or "")).strip()
                result["data_mode"] = "real"
                result["_mock"] = False
        except Exception:
            pass
    return JSONResponse(result)


@app.post("/api/ndvi")
async def ndvi(payload: dict) -> JSONResponse:
    """Végétation NDVI (NASA MODIS) avec un budget dédié + cache Neon permanent.
    Le front l'appelle en arrière-plan : le serveur ORNL est trop lent pour l'analyse
    principale, mais ici on peut l'attendre, puis tout le monde profite du cache."""
    payload = payload or {}
    try:
        lat = float(payload.get("latitude")); lon = float(payload.get("longitude"))
    except (TypeError, ValueError):
        return JSONResponse({"error": "bad_coords"}, status_code=422)
    return JSONResponse(await run_in_threadpool(live_data.warm_ndvi, lat, lon))


@app.post("/api/grid")
async def weather_grid(payload: dict) -> JSONResponse:
    """Grille Open-Meteo autour de la parcelle pour les couches météo du globe
    (pluie 60 j, température et vent actuels, soleil 7 j) — même source que l'analyse."""
    payload = payload or {}
    try:
        lat = float(payload.get("latitude")); lon = float(payload.get("longitude"))
    except (TypeError, ValueError):
        return JSONResponse({"error": "bad_coords"}, status_code=422)
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return JSONResponse({"error": "bad_coords"}, status_code=422)
    try:
        return JSONResponse(await run_in_threadpool(live_data.grid, lat, lon))
    except Exception as e:
        return JSONResponse({"error": type(e).__name__}, status_code=502)


@app.post("/api/ecostress")
async def ecostress_hotspots(payload: dict) -> JSONResponse:
    """Points chauds NASA ECOSTRESS (70 m) : dernier passage de jour sans nuage sur la
    parcelle, image géoréférencée + rang de la parcelle (« plus chaude que X % de la zone »)."""
    payload = payload or {}
    try:
        lat = float(payload.get("latitude")); lon = float(payload.get("longitude"))
    except (TypeError, ValueError):
        return JSONResponse({"error": "bad_coords"}, status_code=422)
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return JSONResponse({"error": "bad_coords"}, status_code=422)
    import ecostress
    try:
        return JSONResponse(await run_in_threadpool(ecostress.hotspots, lat, lon))
    except LookupError as e:  # pas de passage récent, ou nuages sur la parcelle
        return JSONResponse({"error": str(e) or "no_data"}, status_code=404)
    except Exception as e:
        return JSONResponse({"error": type(e).__name__}, status_code=502)


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
    if engine is not None:
        fn = engine.copilot_answer                 # moteur ML complet (dev local)
    elif light_copilot is not None:
        fn = _light_copilot_answer                 # Vercel : Gemini sans le stack ML
    else:
        fn = mock_engine.copilot_answer            # dernier repli déterministe
    result = await run_in_threadpool(
        fn,
        question=str(payload.get("question", "")),
        context=payload.get("context"),
        lang=str(payload.get("lang", "fr")),
    )
    # Diagnostic temporaire : {"debug": true} renvoie l'état du copilote de LA MÊME
    # instance qui vient de répondre (le /health peut tomber sur une autre instance
    # serverless). Ne révèle jamais la clé. À retirer après mise au point.
    if payload.get("debug"):
        try:
            from app import copilot as _cp
            result = {**result, "_diag": _cp.status()}
        except Exception as exc:
            result = {**result, "_diag": {"error": type(exc).__name__}}
    return JSONResponse(result)


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    """La racine ouvre le site public (site.html). L'application commence à /inicio.html."""
    return FileResponse(FRONTEND_DIR / "site.html")


# IMPORTANT : monter les statiques en dernier, pour ne pas masquer les routes /api.
if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
