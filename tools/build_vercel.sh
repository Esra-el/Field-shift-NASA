#!/usr/bin/env bash
# Field Shift — construit le paquet Vercel complet dans dist/vercel :
#   public/          → le front (site public à la racine, application PWA, images), servi par le CDN
#   api/index.py     → le backend FastAPI (données en direct + modèle ML + copilote Gemini)
#   api/_lib/        → modules du backend + paquet app/ du Flux 2 (le « _ » évite que Vercel en fasse des fonctions)
# Déployer ensuite :  cd dist/vercel && vercel deploy --prod --yes
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/dist/vercel"

# Garder le lien vers le projet Vercel (.vercel) entre deux constructions
find "$OUT" -mindepth 1 -maxdepth 1 ! -name .vercel -exec rm -rf {} + 2>/dev/null || true
mkdir -p "$OUT/public" "$OUT/api/_lib"

cp -r "$ROOT/frontend/." "$OUT/public/"
cp "$ROOT/frontend/site.html" "$OUT/public/index.html"   # la racine ouvre le site public
cp "$ROOT/backend/main.py" "$ROOT/backend/mock_engine.py" "$ROOT/backend/live_data.py" "$ROOT/backend/real_engine.py" "$OUT/api/_lib/"
# Moteur ML / Gemini du Flux 2 (modèle entraîné + cache NASA POWER des sites pilotes), sans les tests
cp -r "$ROOT/backend/app" "$OUT/api/_lib/app"
find "$OUT/api/_lib/app" \( -name "__pycache__" -o -name "test_*.py" -o -name "conftest.py" \) -prune -exec rm -rf {} +

cat > "$OUT/api/index.py" <<'PY'
"""Point d'entrée Vercel : l'application FastAPI de backend/main.py."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lib"))

from main import app  # noqa: E402,F401
PY

# Python 3.12 sur Vercel ; scikit-learn 1.6.1 = version avec laquelle risk_model.joblib a été entraîné.
echo "3.12" > "$OUT/.python-version"
cat > "$OUT/requirements.txt" <<'TXT'
fastapi==0.115.5
pydantic>=2.5,<3.0
python-dotenv>=1.0
certifi
requests>=2.31
numpy>=1.26,<2.3
pandas>=2.0,<2.3
scikit-learn==1.6.1
joblib>=1.3
google-genai==1.47.0
TXT

cat > "$OUT/vercel.json" <<'JSON'
{
  "functions": {
    "api/index.py": { "maxDuration": 30, "memory": 1024, "includeFiles": "api/_lib/**" }
  },
  "rewrites": [
    { "source": "/api/(.*)", "destination": "/api/index" }
  ],
  "redirects": [
    { "source": "/site.html", "destination": "/", "permanent": true }
  ],
  "headers": [
    { "source": "/sw.js", "headers": [{ "key": "Cache-Control", "value": "no-cache" }] },
    { "source": "/img/(.*)", "headers": [{ "key": "Cache-Control", "value": "public, max-age=604800" }] }
  ]
}
JSON
echo "Built $OUT"
