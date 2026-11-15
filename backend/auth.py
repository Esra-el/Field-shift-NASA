"""Field Shift — comptes utilisateurs (inscription, connexion, profil).

* Mots de passe : hachés avec scrypt (bibliothèque standard), sel aléatoire par compte.
* Session : jeton signé HMAC-SHA256 (« Bearer »), valable 30 jours.
  Clé de signature : variable d'environnement FIELDSHIFT_SECRET (obligatoire en production).
* Stockage :
    - DATABASE_URL (postgres://…) si défini -> PostgreSQL (psycopg) ;
    - sinon SQLite : FIELDSHIFT_DB, ou backend/data/fieldshift.db en local.
  Les deux partagent le même schéma et les mêmes requêtes.

Le téléphone sert d'identifiant de connexion. L'adresse est géocodée côté client
(Nominatim) : on garde l'adresse, la région, la latitude et la longitude pour que
l'application sache tout de suite où se trouve la parcelle.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

TOKEN_TTL = 30 * 24 * 3600
_LOCK = threading.Lock()

# --------------------------------------------------------------------------- #
# Clé de signature
# --------------------------------------------------------------------------- #
def _secret() -> bytes:
    s = os.environ.get("FIELDSHIFT_SECRET")
    if s:
        return s.encode()
    # Local : clé générée une fois et gardée à côté de la base (jamais commitée).
    p = Path(__file__).resolve().parent / "data" / ".secret"
    try:
        if p.exists():
            return p.read_bytes()
        p.parent.mkdir(parents=True, exist_ok=True)
        key = secrets.token_bytes(32)
        p.write_bytes(key)
        return key
    except OSError:
        # Système de fichiers en lecture seule (serverless sans secret) : clé du processus.
        global _EPHEMERAL
        try:
            return _EPHEMERAL
        except NameError:
            _EPHEMERAL = secrets.token_bytes(32)
            return _EPHEMERAL


# --------------------------------------------------------------------------- #
# Stockage (SQLite ou PostgreSQL)
# --------------------------------------------------------------------------- #
_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id {pk},
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  phone TEXT NOT NULL UNIQUE,
  address TEXT NOT NULL,
  region TEXT,
  country TEXT,
  latitude DOUBLE PRECISION,
  longitude DOUBLE PRECISION,
  pw_hash TEXT NOT NULL,
  created_at BIGINT NOT NULL
)
"""


class _DB:
    def __init__(self) -> None:
        # Neon via Vercel fournit DATABASE_URL (et POSTGRES_URL selon l'intégration).
        url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL") or ""
        self.pg = url.startswith("postgres")
        if self.pg:
            import psycopg  # noqa: F401  (dépendance optionnelle)
            self.url = url
            self.ph = "%s"
        else:
            default = Path(__file__).resolve().parent / "data" / "fieldshift.db"
            path = os.environ.get("FIELDSHIFT_DB") or str(default)
            try:
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                sqlite3.connect(path).close()
            except (OSError, sqlite3.Error):
                path = "/tmp/fieldshift.db"  # serverless : seul /tmp est inscriptible
            self.path = path
            self.ph = "?"
        self._init()

    def _conn(self):
        if self.pg:
            import psycopg
            return psycopg.connect(self.url, autocommit=True)
        c = sqlite3.connect(self.path, timeout=10)
        c.row_factory = sqlite3.Row
        return c

    def _init(self) -> None:
        pk = "SERIAL PRIMARY KEY" if self.pg else "INTEGER PRIMARY KEY AUTOINCREMENT"
        with _LOCK:
            c = self._conn()
            try:
                c.execute(_SCHEMA.format(pk=pk))
                if not self.pg:
                    c.commit()
            finally:
                c.close()

    def q(self, sql: str, args: tuple = (), one: bool = False, write: bool = False):
        sql = sql.replace("?", self.ph)
        with _LOCK:
            c = self._conn()
            try:
                if self.pg:
                    from psycopg.rows import dict_row
                    cur = c.cursor(row_factory=dict_row)
                    cur.execute(sql, args)
                    rows = cur.fetchall() if cur.description else []
                else:
                    cur = c.execute(sql, args)
                    rows = [dict(r) for r in cur.fetchall()] if cur.description else []
                    if write:
                        c.commit()
                return (rows[0] if rows else None) if one else rows
            finally:
                c.close()


_db: _DB | None = None


def db() -> _DB:
    global _db
    if _db is None:
        _db = _DB()
    return _db


def reset_db_for_tests() -> None:
    global _db
    _db = None


# --------------------------------------------------------------------------- #
# Mots de passe et jetons
# --------------------------------------------------------------------------- #
def hash_password(pw: str) -> str:
    salt = secrets.token_bytes(16)
    h = hashlib.scrypt(pw.encode(), salt=salt, n=2 ** 14, r=8, p=1, dklen=32)
    return "scrypt$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(h).decode()


def check_password(pw: str, stored: str) -> bool:
    try:
        _, s, h = stored.split("$")
        salt, want = base64.b64decode(s), base64.b64decode(h)
        got = hashlib.scrypt(pw.encode(), salt=salt, n=2 ** 14, r=8, p=1, dklen=32)
        return hmac.compare_digest(got, want)
    except Exception:
        return False


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def make_token(uid: int) -> str:
    body = _b64(json.dumps({"uid": uid, "exp": int(time.time()) + TOKEN_TTL}).encode())
    sig = _b64(hmac.new(_secret(), body.encode(), hashlib.sha256).digest())
    return body + "." + sig


def read_token(token: str) -> int | None:
    try:
        body, sig = token.split(".")
        want = _b64(hmac.new(_secret(), body.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, want):
            return None
        data = json.loads(_unb64(body))
        if data.get("exp", 0) < time.time():
            return None
        return int(data["uid"])
    except Exception:
        return None


def normalize_phone(p: str) -> str:
    p = (p or "").strip()
    digits = re.sub(r"\D", "", p)
    return ("+" if p.startswith("+") else "") + digits


# --------------------------------------------------------------------------- #
# API
# --------------------------------------------------------------------------- #
router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterIn(BaseModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    phone: str = Field(min_length=6, max_length=24)
    address: str = Field(min_length=2, max_length=240)
    password: str = Field(min_length=6, max_length=128)
    region: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, max_length=80)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class LoginIn(BaseModel):
    phone: str = Field(min_length=6, max_length=24)
    password: str = Field(min_length=1, max_length=128)


class UpdateIn(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=80)
    last_name: str | None = Field(default=None, min_length=1, max_length=80)
    address: str | None = Field(default=None, min_length=2, max_length=240)
    region: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, max_length=80)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    password: str | None = Field(default=None, min_length=6, max_length=128)
    current_password: str | None = Field(default=None, max_length=128)


def _public(u: dict[str, Any]) -> dict[str, Any]:
    return {k: u.get(k) for k in ("id", "first_name", "last_name", "phone", "address", "region",
                                   "country", "latitude", "longitude", "created_at")}


def _user_from(authorization: str | None) -> dict[str, Any]:
    token = (authorization or "").removeprefix("Bearer ").strip()
    uid = read_token(token) if token else None
    if uid is None:
        raise HTTPException(status_code=401, detail="not_authenticated")
    u = db().q("SELECT * FROM users WHERE id = ?", (uid,), one=True)
    if not u:
        raise HTTPException(status_code=401, detail="not_authenticated")
    return u


@router.post("/register")
def register(body: RegisterIn) -> dict[str, Any]:
    phone = normalize_phone(body.phone)
    if len(re.sub(r"\D", "", phone)) < 6:
        raise HTTPException(status_code=422, detail="phone_invalid")
    if db().q("SELECT id FROM users WHERE phone = ?", (phone,), one=True):
        raise HTTPException(status_code=409, detail="phone_taken")
    db().q(
        "INSERT INTO users (first_name, last_name, phone, address, region, country, latitude, longitude, pw_hash, created_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (body.first_name.strip(), body.last_name.strip(), phone, body.address.strip(), body.region,
         body.country, body.latitude, body.longitude, hash_password(body.password), int(time.time())),
        write=True,
    )
    u = db().q("SELECT * FROM users WHERE phone = ?", (phone,), one=True)
    return {"token": make_token(u["id"]), "user": _public(u)}


@router.post("/login")
def login(body: LoginIn) -> dict[str, Any]:
    u = db().q("SELECT * FROM users WHERE phone = ?", (normalize_phone(body.phone),), one=True)
    if not u or not check_password(body.password, u["pw_hash"]):
        raise HTTPException(status_code=401, detail="bad_credentials")
    return {"token": make_token(u["id"]), "user": _public(u)}


@router.get("/me")
def me(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    return {"user": _public(_user_from(authorization))}


@router.put("/me")
def update_me(body: UpdateIn, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    u = _user_from(authorization)
    fields: dict[str, Any] = {}
    for k in ("first_name", "last_name", "address", "region", "country", "latitude", "longitude"):
        v = getattr(body, k)
        if v is not None:
            fields[k] = v.strip() if isinstance(v, str) else v
    if body.password:
        if not body.current_password or not check_password(body.current_password, u["pw_hash"]):
            raise HTTPException(status_code=403, detail="bad_current_password")
        fields["pw_hash"] = hash_password(body.password)
    if fields:
        sets = ", ".join(f"{k} = ?" for k in fields)
        db().q(f"UPDATE users SET {sets} WHERE id = ?", (*fields.values(), u["id"]), write=True)
    return {"user": _public(db().q("SELECT * FROM users WHERE id = ?", (u["id"],), one=True))}


@router.delete("/me")
def delete_me(authorization: str | None = Header(default=None)) -> dict[str, bool]:
    u = _user_from(authorization)
    db().q("DELETE FROM users WHERE id = ?", (u["id"],), write=True)
    return {"deleted": True}
