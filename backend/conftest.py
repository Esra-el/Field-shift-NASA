import os, sys
# Rendre importables backend/main.py, real_engine.py, mock_engine.py et le paquet app/.
sys.path.insert(0, os.path.dirname(__file__))
# Tests hermétiques : pas d'appel réseau en direct (NASA POWER / Open-Meteo / MODIS).
# Le chemin « direct » est testé à part avec des données simulées (tests/test_live.py).
os.environ.setdefault("FIELDSHIFT_LIVE", "0")
# L'analogue 20 ans (NASA POWER même-date) fait son propre appel réseau : coupé par
# défaut pendant les tests. La fonction elle-même est testée dans tests/test_analog.py.
os.environ.setdefault("FIELDSHIFT_ANALOG", "0")
