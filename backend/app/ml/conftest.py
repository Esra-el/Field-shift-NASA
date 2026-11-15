"""Shared fixtures for the ml test lane.

Keeps output pristine (silences the LibreSSL/urllib3 import warning) and makes
the model-backed tests self-heal: if the trained bundle is missing but the raw
NASA cache is present, rebuild it offline — no network in the test run.
"""
from __future__ import annotations

import warnings

import pytest

warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL")


@pytest.fixture(scope="session", autouse=True)
def _ensure_trained_model():
    from app.ml import data as D
    from app.ml import store as ST
    from app.ml import train as T

    if ST.load_bundle() is not None:
        return
    start, end = D.history_range()
    cached = []
    for s in D.GLOBAL_SITES:
        cached.append(D.cache_path(s["latitude"], s["longitude"], start, end))
        cached.append(D.modis_cache_path(s["latitude"], s["longitude"], start, end))
    if all(p.exists() for p in cached):
        T.train()  # offline: both fetchers serve every site from cache
    else:
        pytest.skip("No trained model and no NASA cache; run `python -m app.ml.train`.")
