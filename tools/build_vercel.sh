#!/usr/bin/env bash
# Field Shift — construit le paquet Vercel complet dans dist/vercel :
#   public/          → le front (site public à la racine, application PWA, images), servi par le CDN
#   api/index.py     → le backend FastAPI (API + données en direct NASA POWER / Open-Meteo / MODIS)
#   api/_lib/        → modules du backend (le « _ » évite que Vercel en fasse des fonctions)
# Déployer ensuite :  cd dist/vercel && vercel deploy --prod --yes
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/dist/vercel"

# Garder le lien vers le projet Vercel (.vercel) entre deux constructions
find "$OUT" -mindepth 1 -maxdepth 1 ! -name .vercel -exec rm -rf {} + 2>/dev/null || true
mkdir -p "$OUT/public" "$OUT/api/_lib"

cp -r "$ROOT/frontend/." "$OUT/public/"
cp "$ROOT/frontend/site.html" "$OUT/public/index.html"   # la racine ouvre le site public
cp "$ROOT/backend/main.py" "$ROOT/backend/mock_engine.py" "$ROOT/backend/live_data.py" "$OUT/api/_lib/"

cat > "$OUT/api/index.py" <<'PY'
"""Point d'entrée Vercel : l'application FastAPI de backend/main.py."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lib"))

from main import app  # noqa: E402,F401
PY

cat > "$OUT/requirements.txt" <<'TXT'
fastapi==0.115.5
certifi
TXT

cat > "$OUT/vercel.json" <<'JSON'
{
  "functions": {
    "api/index.py": { "maxDuration": 30, "includeFiles": "api/_lib/**" }
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
