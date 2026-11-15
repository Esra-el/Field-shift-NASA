"""Point d'entrée Vercel (déploiement depuis la racine du dépôt GitHub).

Vercel transforme ce fichier en fonction Python ; toutes les routes /api/* y sont
redirigées (vercel.json). L'application FastAPI vit dans backend/main.py.
Le front (dossier frontend/) est servi en statique par le CDN de Vercel.
"""
import os
import sys

BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
sys.path.insert(0, BACKEND)

from main import app  # noqa: E402,F401
