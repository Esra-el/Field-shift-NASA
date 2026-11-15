"""Field Shift — Aplicación FastAPI (Flux 1).

Responsabilidades de este archivo (volet Producto / Full-Stack):
  * Servir la PWA (archivos estáticos del front).
  * Exponer la API que consume el front, con el formato del contrato 8.6.

Por ahora la API usa un motor MOCK (mock_engine). El Flux 2 reemplazará ese
motor por el pipeline real NASA + ML + IA sin cambiar el formato de respuesta.

Ejecutar:
    cd backend
    uvicorn main:app --reload
Luego abrir:  http://127.0.0.1:8000/
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from fastapi.concurrency import run_in_threadpool

import live_data
from mock_engine import backtesting, copilot_answer, generate_recommendation

FRONTEND_DIR = (Path(__file__).resolve().parent.parent / "frontend")

app = FastAPI(
    title="Field Shift API",
    description="Decisiones de siembra ante la sequía a partir de datos NASA.",
    version="0.1.0-mvp",
)

# CORS abierto en desarrollo (front y back pueden correr por separado).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "field-shift", "mode": "live"}


@app.post("/api/recommendation")
async def recommendation(payload: dict) -> JSONResponse:
    """Devuelve la recomendación completa para un campo (contrato 8.6)."""
    payload = payload or {}
    live = {}
    if payload.get("live", True):
        try:
            lat = float(payload.get("latitude", 14.8)); lon = float(payload.get("longitude", -90.5))
            # NASA POWER + Open-Meteo + MODIS en direct (en parallèle, ~1-12 s, cache 1 h)
            live = await run_in_threadpool(live_data.fetch, lat, lon)
        except (TypeError, ValueError):
            live = {}
    result = generate_recommendation(payload, live)
    return JSONResponse(result)


@app.post("/api/backtesting")
async def backtest(payload: dict) -> JSONResponse:
    """Démo backtesting : saisons sèches passées + « aurait prévenu ? »."""
    return JSONResponse(backtesting(payload or {}))


@app.post("/api/copilot")
async def copilot(payload: dict) -> JSONResponse:
    """Copiloto IA (mock). Entrada: {question, context}."""
    payload = payload or {}
    result = copilot_answer(
        question=str(payload.get("question", "")),
        context=payload.get("context"),
        lang=str(payload.get("lang", "fr")),
    )
    return JSONResponse(result)


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    """La raíz abre el sitio público (site.html). La aplicación empieza en /inicio.html."""
    return FileResponse(FRONTEND_DIR / "site.html")


# IMPORTANTE: montar los estáticos al final, para que no tape las rutas /api.
if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
