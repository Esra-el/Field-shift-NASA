import os, sys
# Rendre importables backend/main.py, real_engine.py, mock_engine.py et le paquet app/.
sys.path.insert(0, os.path.dirname(__file__))
# Tests hermétiques : pas d'appel réseau en direct (NASA POWER / Open-Meteo / MODIS).
# Le chemin « direct » est testé à part avec des données simulées (tests/test_live.py).
os.environ.setdefault("FIELDSHIFT_LIVE", "0")
