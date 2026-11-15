"""Comptes : inscription, connexion, profil, mot de passe, suppression (SQLite temporaire)."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("FIELDSHIFT_DB", str(tmp_path / "t.db"))
    monkeypatch.setenv("FIELDSHIFT_SECRET", "test-secret")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    import auth
    auth.reset_db_for_tests()
    import main
    return TestClient(main.app)


NEW = {"first_name": "Ana", "last_name": "López", "phone": "+504 9999-0001", "address": "Choluteca, Honduras",
       "password": "secret12", "region": "Choluteca", "country": "Honduras", "latitude": 13.3, "longitude": -87.19}


def test_register_login_me_update_delete(client):
    r = client.post("/api/auth/register", json=NEW)
    assert r.status_code == 200
    tok = r.json()["token"]
    u = r.json()["user"]
    assert u["phone"] == "+50499990001" and u["region"] == "Choluteca" and "pw_hash" not in u

    # Même téléphone (autre format) : refusé
    assert client.post("/api/auth/register", json={**NEW, "phone": "+504 9999 0001"}).status_code == 409

    # Connexion
    assert client.post("/api/auth/login", json={"phone": "+50499990001", "password": "bad"}).status_code == 401
    r = client.post("/api/auth/login", json={"phone": "+504-9999-0001", "password": "secret12"})
    assert r.status_code == 200
    h = {"Authorization": "Bearer " + r.json()["token"]}

    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer x.y"}).status_code == 401
    assert client.get("/api/auth/me", headers=h).json()["user"]["first_name"] == "Ana"

    # Profil et mot de passe
    r = client.put("/api/auth/me", headers=h, json={"address": "Somotillo, Nicaragua", "region": "Chinandega"})
    assert r.json()["user"]["region"] == "Chinandega"
    assert client.put("/api/auth/me", headers=h, json={"password": "nouveau1", "current_password": "faux"}).status_code == 403
    assert client.put("/api/auth/me", headers=h, json={"password": "nouveau1", "current_password": "secret12"}).status_code == 200
    assert client.post("/api/auth/login", json={"phone": NEW["phone"], "password": "nouveau1"}).status_code == 200

    # Suppression
    assert client.delete("/api/auth/me", headers={"Authorization": "Bearer " + tok}).json() == {"deleted": True}
    assert client.get("/api/auth/me", headers=h).status_code == 401


def test_register_validation(client):
    assert client.post("/api/auth/register", json={**NEW, "password": "123"}).status_code == 422
    assert client.post("/api/auth/register", json={**NEW, "first_name": ""}).status_code == 422
    assert client.post("/api/auth/register", json={**NEW, "phone": "abc-def-ghi"}).status_code == 422
