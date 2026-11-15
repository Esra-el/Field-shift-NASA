"""Model persistence — OWNED BY THE `ml` AGENT.

A tiny joblib wrapper kept separate from train.py so risk.py can load the model
without importing the training / network code.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import joblib

# app/ml/store.py -> app/ml/risk_model.joblib
MODEL_PATH = Path(__file__).resolve().parent / "risk_model.joblib"


def save_bundle(bundle: dict, path: Path = MODEL_PATH) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, path)
    return path


def load_bundle(path: Path = MODEL_PATH) -> Optional[dict]:
    path = Path(path)
    if not path.exists():
        return None
    return joblib.load(path)
