"""Tests for the NASA POWER fetch+cache layer.

No real network here: we monkeypatch the HTTP getter so the suite is fast and
deterministic, and we prove the cache is actually used (the demo must never
depend on the live API).
"""
from __future__ import annotations

import json

from app.ml import data as D


def _fake_payload(lat, lon):
    return {
        "properties": {"parameter": {"PRECTOTCORR": {"20100101": 1.0}}},
        "geometry": {"coordinates": [lon, lat, 0]},
    }


def test_cache_path_is_stable_and_descriptive(tmp_path):
    p = D.cache_path(14.8, -90.5, "20040101", "20241231", cache_dir=tmp_path)
    assert p.parent == tmp_path
    # same inputs -> same path (so a cached file is found next run)
    assert p == D.cache_path(14.8, -90.5, "20040101", "20241231", cache_dir=tmp_path)
    assert "14.8" in p.name and "-90.5" in p.name


def test_fetch_writes_cache_then_serves_from_disk(tmp_path, monkeypatch):
    calls = {"n": 0}

    def fake_get(url, params):
        calls["n"] += 1
        return _fake_payload(params["latitude"], params["longitude"])

    monkeypatch.setattr(D, "_http_get_json", fake_get)

    first = D.fetch_power(14.8, -90.5, "20040101", "20241231", cache_dir=tmp_path)
    assert first["geometry"]["coordinates"][:2] == [-90.5, 14.8]
    assert calls["n"] == 1

    # file landed on disk...
    p = D.cache_path(14.8, -90.5, "20040101", "20241231", cache_dir=tmp_path)
    assert p.exists()
    assert json.loads(p.read_text())["properties"]["parameter"]

    # ...and a second call is served from cache (no extra HTTP call)
    second = D.fetch_power(14.8, -90.5, "20040101", "20241231", cache_dir=tmp_path)
    assert second == first
    assert calls["n"] == 1


def test_fetch_uses_cache_even_if_network_would_fail(tmp_path, monkeypatch):
    p = D.cache_path(13.2, -86.1, "20040101", "20241231", cache_dir=tmp_path)
    p.write_text(json.dumps(_fake_payload(13.2, -86.1)))

    def boom(url, params):
        raise AssertionError("network must not be touched when cache exists")

    monkeypatch.setattr(D, "_http_get_json", boom)
    got = D.fetch_power(13.2, -86.1, "20040101", "20241231", cache_dir=tmp_path)
    assert got["geometry"]["coordinates"][:2] == [-86.1, 13.2]
