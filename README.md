# Field Shift 🌱

**Decide qué sembrar antes de la sequía, no después.**

PWA de apoyo a la decisión para agricultores: convierte datos NASA en una
decisión práctica de siembra.

> NASA data → Presupuesto de agua → Línea de siembra → Plan de rotación

NASA Space Apps Challenge · Reto *Field Shift — Adapting Farms with NASA Data*.
Región piloto: Corredor Seco Centroamericano (Guatemala, Honduras, Nicaragua).

---

## Estado actual (Flux 1 + Flux 2 integrados)

- **Flux 1 — Producto / Full-Stack** (Zlat): la PWA completa + el backend FastAPI
  que la sirve y expone la API (contrato §8.6).
- **Flux 2 — Datos / ML / IA** (esra): el **motor real** detrás de esa misma API
  — NASA POWER (lluvia, radiación, ET, temperatura), modelo ML de riesgo de
  sequía, y copiloto IA con **Google Gemini** (nivel gratuito). Reemplaza el
  motor mock **sin cambiar el formato de la API**, así que el front no cambia una
  línea. `mock_engine.py` queda como **fallback** automático: si faltan datos o
  falla algo, la demo nunca se cae.

Cada respuesta trae `data_mode` (`"real"` / `"mock"`) y `_mock` para decir
honestamente si los indicadores son reales (NASA POWER en caché para los sitios
piloto) o un sustituto sintético.

### Ya funciona
- Páginas: Inicio, Campo (mapa Leaflet), Perfil, Panel, Análisis, Plan,
  Copiloto, Backtesting, Cooperativa.
- Puntaje de riesgo (ML), presupuesto de agua, línea de siembra, 3 rotaciones.
- Gráficos (Chart.js) e indicadores NASA **reales** (POWER) con proxies
  documentados para humedad de suelo / NDVI.
- Copiloto IA **real** (Gemini, con fallback) y tarjeta de cooperativa con QR.
- Backtesting **real**: el modelo re-evalúa las sequías pasadas (El Niño
  2015-16 / 2023-24) sobre el historial POWER del sitio.
- Interfaz **trilingüe FR / EN / IT**.
- PWA: manifiesto + service worker + modo sin conexión.

---

## Cómo ejecutar

Requisitos: Python 3.10+.

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Abrir: <http://127.0.0.1:8000/>

El backend sirve el front y la API en el mismo origen, así que no hay que
configurar nada más.

**Copiloto IA en vivo (opcional):** poné una clave gratuita de Google AI Studio
en `backend/.env` como `GEMINI_API_KEY=...` (o `GOOGLE_API_KEY`). Sin clave, el
copiloto sigue respondiendo con su fallback determinista. El archivo `.env`
está en `.gitignore` — **no se commitea**.

Los datos reales de NASA POWER para los 3 sitios piloto vienen **en caché**
(`backend/app/data/cache/`), así que `data_mode: "real"` funciona sin red. Para
un punto no cacheado, exportá `FIELDSHIFT_ALLOW_FETCH=1` para que busque en vivo
(si no, cae a sintético).

---

## Estructura

```
field-shift/
├── backend/
│   ├── main.py          # FastAPI: sirve el front + API (/api/*)
│   ├── real_engine.py   # Flux 2: motor REAL (NASA POWER + ML + Gemini)
│   ├── mock_engine.py   # motor MOCK (fallback automático, trilingüe)
│   ├── app/             # pipeline Flux 2: schemas, engines/, ml/, data/, copilot
│   │   ├── ml/risk_model.joblib   # modelo entrenado (63 temporadas-sitio)
│   │   └── data/cache/            # NASA POWER en caché (3 sitios piloto)
│   ├── tests/           # contrato front↔API + copiloto + ml
│   └── requirements.txt
└── frontend/
    ├── index.html  campo.html  perfil.html
    ├── panel.html  copiloto.html  cooperativa.html
    ├── css/app.css
    ├── js/          # i18n, store, api, pwa + lógica por página
    ├── icons/icon.svg
    ├── manifest.webmanifest
    └── sw.js
```

---

## Contrato de API (frontend ↔ Flux 2)

**No cambiar sin avisar al equipo** (regla de colaboración del documento).

`POST /api/recommendation`

Entrada:
```json
{ "latitude": 14.8, "longitude": -90.5, "crop": "maize",
  "soil_type": "sandy_loam", "irrigation": false, "priority": "save_water" }
```

Salida (misma forma en el motor real y en el mock): `risk_score`, `risk_level`,
`water_budget` (con `coverage_pct`), `planting_timeline`, `rotations`,
`nasa_indicators`, `ai_explanation`, `series` (8 semanas para los gráficos),
`risk_components` (el "por qué" del riesgo), `data_mode` y `_mock`.

`POST /api/copilot` → `{ question, context, lang }` → `{ answer, sources, limitations }`
(copiloto **Gemini**, con fallback).

`POST /api/backtesting` → `{ ...payload, lang }` → `{ seasons[], summary, warned_count, total }`.

---

## Reparto del trabajo

| Flux | Persona | Alcance |
|---|---|---|
| **1** | Producto / Full-Stack | PWA, páginas, mapa, gráficos, integración front↔API, demo |
| **2** | Datos / ML / IA | Conectores NASA, indicadores, motores de riesgo/agua/siembra/rotación, ML, copiloto IA, backtesting |

El límite entre ambos es el **contrato de API** de arriba.
