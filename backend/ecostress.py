"""Field Shift — points chauds de la parcelle avec NASA ECOSTRESS (70 m).

ECOSTRESS mesure la température de surface depuis la Station spatiale. Les fichiers
de valeurs demandent un compte Earthdata, mais NASA LP DAAC publie pour chaque
passage une image d'aperçu PUBLIQUE et géoréférencée (UTM) de la température de
surface (produit ECO_L2T_LSTE). Cette image est en couleurs « jet » étirées sur la
tuile : elle ne donne pas des degrés, mais elle montre très bien où il fait PLUS
CHAUD ou PLUS FRAIS qu'autour, ce qui sert à repérer le stress des cultures.

Ce module :
  1. cherche les passages récents au-dessus du point (NASA CMR, sans clé) ;
  2. garde le plus récent de JOUR où la parcelle n'est pas sous les nuages ;
  3. renvoie l'image (nuages/sans donnée rendus transparents), ses 4 coins en
     latitude/longitude, et le rang de la parcelle : « plus chaude que X % de la zone ».
"""
from __future__ import annotations

import base64
import io
import json
import math
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any

try:
    import certifi, ssl
    _SSL = ssl.create_default_context(cafile=certifi.where())
except Exception:  # pragma: no cover
    import ssl
    _SSL = ssl.create_default_context()

UA = {"User-Agent": "FieldShift/1.0 (NASA Space Apps demo)"}
CMR = "https://cmr.earthdata.nasa.gov/search/granules.umm_json"
_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_TTL = 6 * 3600


def _get(url: str, params: dict[str, Any] | None = None, timeout: int = 20) -> bytes:
    full = url + ("?" + urllib.parse.urlencode(params) if params else "")
    req = urllib.request.Request(full, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout, context=_SSL) as r:
        return r.read()


# --- UTM -> latitude/longitude (WGS 84), formule inverse classique ---------------------
def utm_to_latlon(e: float, n: float, zone: int, north: bool = True) -> tuple[float, float]:
    a, f = 6378137.0, 1 / 298.257223563
    k0 = 0.9996
    e2 = f * (2 - f)
    ep2 = e2 / (1 - e2)
    x = e - 500000.0
    y = n if north else n - 10000000.0
    m = y / k0
    mu = m / (a * (1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256))
    e1 = (1 - math.sqrt(1 - e2)) / (1 + math.sqrt(1 - e2))
    p1 = (mu + (3 * e1 / 2 - 27 * e1 ** 3 / 32) * math.sin(2 * mu)
          + (21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32) * math.sin(4 * mu)
          + (151 * e1 ** 3 / 96) * math.sin(6 * mu) + (1097 * e1 ** 4 / 512) * math.sin(8 * mu))
    c1 = ep2 * math.cos(p1) ** 2
    t1 = math.tan(p1) ** 2
    n1 = a / math.sqrt(1 - e2 * math.sin(p1) ** 2)
    r1 = a * (1 - e2) / (1 - e2 * math.sin(p1) ** 2) ** 1.5
    d = x / (n1 * k0)
    lat = p1 - (n1 * math.tan(p1) / r1) * (d ** 2 / 2 - (5 + 3 * t1 + 10 * c1 - 4 * c1 ** 2 - 9 * ep2) * d ** 4 / 24
                                          + (61 + 90 * t1 + 298 * c1 + 45 * t1 ** 2 - 252 * ep2 - 3 * c1 ** 2) * d ** 6 / 720)
    lon = (d - (1 + 2 * t1 + c1) * d ** 3 / 6 + (5 - 2 * c1 + 28 * t1 - 3 * c1 ** 2 + 8 * ep2 + 24 * t1 ** 2) * d ** 5 / 120) / math.cos(p1)
    lon0 = (zone - 1) * 6 - 180 + 3
    return math.degrees(lat), lon0 + math.degrees(lon)


def latlon_to_utm(lat: float, lon: float, zone: int) -> tuple[float, float]:
    """Sens direct (pour trouver le pixel de la parcelle dans l'image)."""
    a, f = 6378137.0, 1 / 298.257223563
    k0 = 0.9996
    e2 = f * (2 - f)
    ep2 = e2 / (1 - e2)
    lat_r = math.radians(lat)
    lon0 = math.radians((zone - 1) * 6 - 180 + 3)
    n = a / math.sqrt(1 - e2 * math.sin(lat_r) ** 2)
    t = math.tan(lat_r) ** 2
    c = ep2 * math.cos(lat_r) ** 2
    aa = math.cos(lat_r) * (math.radians(lon) - lon0)
    m = a * ((1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256) * lat_r
             - (3 * e2 / 8 + 3 * e2 ** 2 / 32 + 45 * e2 ** 3 / 1024) * math.sin(2 * lat_r)
             + (15 * e2 ** 2 / 256 + 45 * e2 ** 3 / 1024) * math.sin(4 * lat_r)
             - (35 * e2 ** 3 / 3072) * math.sin(6 * lat_r))
    e = k0 * n * (aa + (1 - t + c) * aa ** 3 / 6 + (5 - 18 * t + t ** 2 + 72 * c - 58 * ep2) * aa ** 5 / 120) + 500000.0
    nn = k0 * (m + n * math.tan(lat_r) * (aa ** 2 / 2 + (5 - t + 9 * c + 4 * c ** 2) * aa ** 4 / 24
                                          + (61 - 58 * t + t ** 2 + 600 * c - 330 * ep2) * aa ** 6 / 720))
    if lat < 0:
        nn += 10000000.0
    return e, nn


# --- Palette « jet » : couleur -> position 0 (frais) .. 1 (chaud) ------------------------
def _jet(v: float) -> tuple[int, int, int]:
    r = min(1.0, max(0.0, 1.5 - abs(4 * v - 3)))
    g = min(1.0, max(0.0, 1.5 - abs(4 * v - 2)))
    b = min(1.0, max(0.0, 1.5 - abs(4 * v - 1)))
    return int(r * 255), int(g * 255), int(b * 255)


_JET = [(i / 255, _jet(i / 255)) for i in range(256)]


def jet_value(rgb: tuple[int, int, int]) -> float | None:
    """Position sur la palette jet ; None si noir/gris (nuage ou sans donnée)."""
    r, g, b = rgb[:3]
    if max(r, g, b) < 60:
        return None
    best = min(_JET, key=lambda p: (p[1][0] - r) ** 2 + (p[1][1] - g) ** 2 + (p[1][2] - b) ** 2)
    return best[0]


def _granules(lat: float, lon: float, days: int = 40) -> list[dict[str, Any]]:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    raw = _get(CMR, {"short_name": "ECO_L2T_LSTE", "point": f"{lon:.5f},{lat:.5f}", "sort_key": "-start_date",
                     "page_size": 12, "temporal": f"{start:%Y-%m-%dT%H:%M:%SZ},{end:%Y-%m-%dT%H:%M:%SZ}"}, timeout=15)
    out = []
    for it in json.loads(raw).get("items", []):
        u = it["umm"]
        t0 = u["TemporalExtent"]["RangeDateTime"]["BeginningDateTime"]
        urls = [x["URL"] for x in u.get("RelatedUrls", []) if x.get("URL", "").startswith("https://")
                and x["URL"].endswith("_LST.jpeg") and "lp-prod-public" in x["URL"]]
        if urls:
            out.append({"id": u.get("GranuleUR"), "time": t0, "jpeg": urls[0]})
    return out


def _local_hour(utc_iso: str, lon: float) -> float:
    t = datetime.fromisoformat(utc_iso.replace("Z", "+00:00"))
    return (t.hour + t.minute / 60 + lon / 15) % 24


def hotspots(lat: float, lon: float, max_tries: int = 6) -> dict[str, Any]:
    """Dernier passage ECOSTRESS de jour, sans nuage sur la parcelle. Lève une exception si rien."""
    from PIL import Image  # dépendance déjà présente (Pillow via les libs du projet)

    key = f"{round(lat, 3)}:{round(lon, 3)}"
    hit = _CACHE.get(key)
    if hit and time.time() - hit[0] < _TTL:
        return hit[1]
    grans = _granules(lat, lon)
    if not grans:
        raise LookupError("no_overpass")
    # D'abord les passages de jour (8 h - 17 h locales), du plus récent au plus ancien.
    day = [g for g in grans if 8 <= _local_hour(g["time"], lon) <= 17]
    order = (day + [g for g in grans if g not in day])[:max_tries]
    last_err = "no_clear_day_pass"

    def _fetch(g):
        return _get(g["jpeg"], timeout=12), _get(g["jpeg"] + ".aux.xml", timeout=12).decode("utf-8", "ignore")

    # Téléchargements en parallèle (budget serverless ~30 s), puis examen dans l'ordre.
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=len(order) or 1) as pool:
        futs = [pool.submit(_fetch, g) for g in order]
        fetched = []
        for g, fu in zip(order, futs):
            try:
                fetched.append((g, *fu.result(timeout=16)))
            except Exception as e:  # réseau / fichier absent
                last_err = type(e).__name__
    for g, jpeg, aux in fetched:
        gt = re.search(r"<GeoTransform>\s*([^<]+)</GeoTransform>", aux)
        zone_m = re.search(r"UTM zone (\d+)([NS])", aux)
        if not gt or not zone_m:
            continue
        x0, dx, _, y0, _, dy = [float(v) for v in gt.group(1).split(",")]
        zone, north = int(zone_m.group(1)), zone_m.group(2) == "N"
        im = Image.open(io.BytesIO(jpeg)).convert("RGB")
        w, h = im.size
        e, n = latlon_to_utm(lat, lon, zone)
        if not north and lat >= 0:
            n -= 10000000.0
        px, py = int((e - x0) / dx), int((n - y0) / dy)
        if not (0 <= px < w and 0 <= py < h):
            continue
        # Valeur de la parcelle : moyenne sur ~3x3 pixels (≈ 200 m) non nuageux.
        field_vals = [jet_value(im.getpixel((min(w - 1, max(0, px + i)), min(h - 1, max(0, py + j)))))
                      for i in (-1, 0, 1) for j in (-1, 0, 1)]
        field_vals = [v for v in field_vals if v is not None]
        if len(field_vals) < 5:
            last_err = "cloud_over_field"
            continue
        field_v = sum(field_vals) / len(field_vals)
        # Rang de la parcelle dans une zone de ~10 km autour (pixels valides).
        rad = int(5000 / abs(dx))
        small = im.crop((max(0, px - rad), max(0, py - rad), min(w, px + rad), min(h, py + rad))).resize((80, 80))
        zone_vals = [v for v in (jet_value(p) for p in small.getdata()) if v is not None]
        if len(zone_vals) < 200:
            last_err = "cloudy_area"
            continue
        pct = round(100 * sum(1 for v in zone_vals if v < field_v) / len(zone_vals))
        # Image allégée et transparente là où il n'y a pas de donnée (nuages, nuit, mer).
        thumb = im.resize((min(560, w), min(560, h)))
        rgba = Image.new("RGBA", thumb.size)
        rgba.putdata([(r, g_, b, 0 if max(r, g_, b) < 60 else 255) for r, g_, b in thumb.getdata()])
        buf = io.BytesIO()
        rgba.save(buf, format="WEBP", quality=70, method=4)
        corners = [utm_to_latlon(x0 + cx * dx * w, y0 + cy * dy * h, zone, north) for cx, cy in ((0, 0), (1, 0), (1, 1), (0, 1))]
        out = {
            "time": g["time"], "local_hour": round(_local_hour(g["time"], lon), 1), "granule": g["id"],
            "field_percentile": pct, "coordinates": [[round(lo, 5), round(la, 5)] for la, lo in corners],
            "image": "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode("ascii"),
            "source": "NASA ECOSTRESS ECO_L2T_LSTE (70 m)",
        }
        _CACHE[key] = (time.time(), out)
        return out
    raise LookupError(last_err)
