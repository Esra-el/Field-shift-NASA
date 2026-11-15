# Field Shift 🌱

**Crop rotations that save water and protect the soil, worked out for each field from live NASA Earth data.**

NASA Space Apps Challenge 2026 · Rome · Challenge *Field Shift: Adapting Farms with NASA Data*

- **Live app:** https://shift-field.vercel.app (no account needed: **Try it without an account**, or open [/globo.html?demo=1](https://shift-field.vercel.app/globo.html?demo=1))
- **Demo deck (PDF):** [docs/Field-Shift-demo.pdf](docs/Field-Shift-demo.pdf)

## What it does

A farmer gives their field, crop, soil, water access, priority and **current rotation**. Field Shift then:

1. **Reads the field's conditions**: rain over the last 60 days vs. the normal, soil and root-zone moisture, vegetation trend, temperature, slope, surface hot spots.
2. **Scores 16 crops** (cereals, legumes, cover crops…) on this field's temperature normals, expected rain and frost risk, and picks each one's sowing date.
3. **Builds 3 rotations** (safest, balanced, highest yield) and compares them with the farmer's **current rotation**, using the same calculations. Cover crops fill the gaps so the soil is not left bare.
4. **Explains every plan**: the data behind it, what we don't know, and what to check locally. The tool supports the farmer's judgment; it does not replace it.

It also shows a 3D globe with the data layers, a water budget, a planting window, a drought-risk score from a machine-learning model, and an AI assistant (Gemini). The app works on phones, offline, in English, French and Italian.

## Data

| Source | Used for |
|---|---|
| **NASA POWER** | Temperature normals and anomalies, root-zone wetness, history for the risk model |
| **NASA SMAP L4** | Root-zone soil moisture map |
| **NASA MODIS MOD13Q1 · VIIRS** | Vegetation (NDVI) trend and map |
| **NASA SRTM** | Field slope → erosion risk |
| **NASA ECOSTRESS** | 70 m surface hot spots (relative) |
| ERA5 (ECMWF) | Rainfall normal 1991–2020 |
| Open-Meteo | Recent rain, forecast, FAO-56 evapotranspiration, weather grid |

We checked the numbers against independent forecasts (MET Norway, ECMWF, ERA5) in 6 locations: Rome, Paris, Brazzaville, Dakar, Nairobi and Guatemala.

## Run locally

```bash
cd backend
python -m venv .venv && .venv/Scripts/activate   # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload                        # → http://127.0.0.1:8000
```

Optional: `GEMINI_API_KEY=…` in `backend/.env` for the AI assistant (it falls back to built-in answers without a key). Tests: `pytest` in `backend/`.

## Code

- `backend/`: FastAPI. `live_data.py` (live data), `rotations.py` (rotation engine), `ecostress.py`, `mock_engine.py` (analysis), `app/ml/` (risk model)
- `frontend/`: web app (MapLibre globe, pages, offline service worker)

## Limits

Crop values are general averages, not local varieties. ECOSTRESS gives relative hot spots, not degrees. Markets and measured soil data are not included yet.

**Team:** Zlat (product, full-stack) · Esra (data, ML, AI)
