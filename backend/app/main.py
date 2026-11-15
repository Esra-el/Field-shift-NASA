"""Field Shift API — FastAPI application entrypoint.

Run (dev):
    uvicorn app.main:app --reload
Then open http://127.0.0.1:8000/docs for the interactive, testable contract.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router

# Load .env (API keys) if present, so a plain `uvicorn app.main:app` picks up
# GEMINI_API_KEY for the live copilot. No-op if python-dotenv or .env is absent.
try:
    from pathlib import Path
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except Exception:
    pass

app = FastAPI(
    title="Field Shift API",
    version="0.1.0",
    description=(
        "Turns NASA Earth-observation data into a planting decision: drought-risk "
        "score, water budget, planting timeline, and crop-rotation plans. "
        "Currently serving MOCK data behind the real §8.6 contract."
    ),
)

# Dev CORS: the PWA frontend runs on a different origin, so let it call this API.
# Tighten allow_origins to the real frontend URL before any public deploy.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/", tags=["meta"])
def root():
    return {
        "name": "Field Shift API",
        "version": "0.1.0",
        "data_mode": "mock",
        "docs": "/docs",
        "recommend": "POST /recommend",
    }
