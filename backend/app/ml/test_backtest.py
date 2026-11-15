"""Tests for the held-out backtest over the known Dry-Corridor drought years."""
from __future__ import annotations

from app.ml import risk
from app.ml import train as T


def test_backtest_covers_every_known_drought_year():
    bt = T.backtest()
    assert bt["drought_years"], "backtest produced no drought-year verdicts"
    # every verdict is a known drought year, with a usable score + flag
    years_seen = set()
    for key, v in bt["drought_years"].items():
        assert v["year"] in T.KNOWN_DROUGHT_YEARS
        assert 0 <= v["risk_score"] <= 100
        assert isinstance(v["flagged_elevated"], bool)
        years_seen.add(v["year"])
    # all four El Nino years are represented across the pilot sites
    assert years_seen == T.KNOWN_DROUGHT_YEARS


def test_backtest_flags_most_drought_years_elevated():
    bt = T.backtest()
    assert 0.0 <= bt["hit_rate"] <= 1.0
    assert bt["hit_rate"] >= 0.5, "model should flag at least half of drought seasons"


def test_backtest_compares_the_supervised_models():
    bt = T.backtest()
    assert set(bt["models"]) == {"random_forest", "logistic_regression", "naive_bayes"}
    for m in bt["models"].values():
        assert {"accuracy", "precision", "recall"} <= set(m)


def test_backtest_documents_proxy_labels():
    bt = T.backtest()
    assert "proxy" in bt["proxy_label_note"].lower()


def test_risk_module_reexports_backtest():
    bt = risk.backtest()
    assert "drought_years" in bt
