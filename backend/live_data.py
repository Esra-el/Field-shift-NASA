"""Field Shift — données réelles, en direct, pour une parcelle.

Trois sources gratuites, sans clé :
- NASA POWER (power.larc.nasa.gov) : pluie journalière (IMERG/MERRA-2 corrigé),
  température, rayonnement solaire, humidité de la zone racinaire (GWETROOT),
  et la normale climatologique de pluie (1981-2020).
- Open-Meteo (open-meteo.com) : météo actuelle, prévision de pluie à 16 jours,
  évapotranspiration FAO-56, humidité du sol. Comble aussi les 2-3 derniers jours
  que NASA POWER n'a pas encore publiés.
- NASA MODIS MOD13Q1 via ORNL DAAC (modis.ornl.gov) : NDVI 250 m, composites 16 jours.

Chaque source est appelée en parallèle avec un délai court. Si l'une échoue,
on renvoie ce qu'on a : le moteur complète avec une estimation et le signale.
Résultats gardés 1 h en mémoire par point (≈ 1 km).
"""
from __future__ import annotations

import json
import ssl
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from typing import Any

try:  # magasin de certificats Mozilla : nécessaire sur Vercel pour modis.ornl.gov (racine emSign)
    import certifi
    _SSL = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL = ssl.create_default_context()

UA = {"User-Agent": "FieldShift/1.0 (NASA Space Apps demo)"}
TIMEOUT = 14
_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_TTL = 3600
# NDVI MODIS : composites tous les 16 jours, serveur ORNL parfois lent -> cache 24 h,
# et si la réponse arrive après le délai, elle est gardée pour la prochaine analyse.
_NDVI: dict[str, tuple[float, list]] = {}
_NDVI_TTL = 86400
_POOL = ThreadPoolExecutor(max_workers=8)
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def _get(url: str, params: dict[str, Any]) -> dict[str, Any]:
    full = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(full, headers=UA)
    with urllib.request.urlopen(req, timeout=TIMEOUT, context=_SSL) as r:
        return json.loads(r.read().decode("utf-8"))


def _power_daily(lat: float, lon: float, start: date, end: date) -> dict[str, Any]:
    d = _get("https://power.larc.nasa.gov/api/temporal/daily/point", {
        "parameters": "PRECTOTCORR,T2M,ALLSKY_SFC_SW_DWN,GWETROOT",
        "community": "AG", "latitude": round(lat, 4), "longitude": round(lon, 4),
        "start": start.strftime("%Y%m%d"), "end": end.strftime("%Y%m%d"), "format": "JSON",
    })
    p = d["properties"]["parameter"]
    out: dict[str, dict[str, float]] = {}
    for key, series in p.items():
        out[key] = {datetime.strptime(k, "%Y%m%d").date().isoformat(): v
                    for k, v in series.items() if v is not None and v > -900}
    return out


def _power_clim(lat: float, lon: float) -> dict[str, float]:
    d = _get("https://power.larc.nasa.gov/api/temporal/climatology/point", {
        "parameters": "PRECTOTCORR,T2M", "community": "AG",
        "latitude": round(lat, 4), "longitude": round(lon, 4), "format": "JSON",
    })
    p = d["properties"]["parameter"]
    out = dict(p["PRECTOTCORR"])  # mm/jour, moyenne par mois
    out["_T2M"] = p.get("T2M") or {}  # température moyenne par mois (°C)
    return out


def _open_meteo(lat: float, lon: float) -> dict[str, Any]:
    return _get("https://api.open-meteo.com/v1/forecast", {
        "latitude": round(lat, 4), "longitude": round(lon, 4),
        "current": "temperature_2m,wind_speed_10m,wind_direction_10m,precipitation,relative_humidity_2m",
        "daily": "precipitation_sum,et0_fao_evapotranspiration,temperature_2m_mean,temperature_2m_max,shortwave_radiation_sum",
        "hourly": "soil_moisture_9_to_27cm",
        "past_days": 60, "forecast_days": 16, "timezone": "auto",
    })


def _modis_code(d: date) -> str:
    return f"A{d.year}{d.timetuple().tm_yday:03d}"


def _ndvi(lat: float, lon: float, today: date) -> list[tuple[str, float]]:
    d = _get("https://modis.ornl.gov/rst/api/v1/MOD13Q1/subset", {
        "latitude": round(lat, 4), "longitude": round(lon, 4), "band": "250m_16_days_NDVI",
        "startDate": _modis_code(today - timedelta(days=96)), "endDate": _modis_code(today),
        "kmAboveBelow": 0, "kmLeftRight": 0,
    })
    pts = []
    for x in d.get("subset", []):
        v = x["data"][0] if x.get("data") else None
        if v is not None and v > -2000:
            pts.append((x["calendar_date"], round(v * 0.0001, 3)))
    return sorted(pts)


# NDVI (MODIS) : le serveur NASA ORNL est lent (18-55 s), trop pour une requête
# serverless (budget ~12 s). On garde donc le NDVI d'une région dans la base Neon
# (partagée, permanente) : récupéré une fois par /api/ndvi, puis servi à tout le
# monde instantanément, même après un redémarrage. Composite tous les 16 jours ->
# le garder 14 jours est correct. Sans base, repli sur le cache mémoire.
_NDVI_DB_TTL = 14 * 86400


def _ndvi_key(lat: float, lon: float) -> str:
    return f"{round(lat, 2)}:{round(lon, 2)}"


def _db():
    try:
        import auth
        d = auth.db()
        d.q("CREATE TABLE IF NOT EXISTS ndvi_cache (k TEXT PRIMARY KEY, pts TEXT NOT NULL, fetched_at BIGINT NOT NULL)", write=True)
        return d
    except Exception:
        return None


def _ndvi_db_get(key: str) -> list | None:
    d = _db()
    if not d:
        return None
    try:
        row = d.q("SELECT pts, fetched_at FROM ndvi_cache WHERE k = ?", (key,), one=True)
        if row and time.time() - row["fetched_at"] < _NDVI_DB_TTL:
            return [tuple(p) for p in json.loads(row["pts"])]
    except Exception:
        pass
    return None


def _ndvi_db_put(key: str, pts: list) -> None:
    d = _db()
    if not d or not pts:
        return
    try:
        payload = json.dumps(pts)
        now = int(time.time())
        if d.pg:
            d.q("INSERT INTO ndvi_cache (k, pts, fetched_at) VALUES (?, ?, ?) "
                "ON CONFLICT (k) DO UPDATE SET pts = EXCLUDED.pts, fetched_at = EXCLUDED.fetched_at",
                (key, payload, now), write=True)
        else:
            d.q("INSERT OR REPLACE INTO ndvi_cache (k, pts, fetched_at) VALUES (?, ?, ?)", (key, payload, now), write=True)
    except Exception:
        pass


def warm_ndvi(lat: float, lon: float) -> dict[str, Any]:
    """Récupère le NDVI avec un budget dédié (jusqu'à ~25 s) et le garde dans Neon.
    Appelé par /api/ndvi, en arrière-plan côté front. Ne lève jamais d'exception."""
    key = _ndvi_key(lat, lon)
    cached = _ndvi_db_get(key)
    if cached:
        last = cached[-1]
        return {"ndvi": last[1], "date": last[0], "cached": True}
    try:
        fut = _POOL.submit(_ndvi, lat, lon, date.today())
        pts = fut.result(timeout=26)
    except Exception as e:
        return {"error": (type(e).__name__)[:60]}
    if not pts:
        return {"error": "no_data"}
    _ndvi_db_put(key, pts)
    _NDVI[key] = (time.time(), pts)
    return {"ndvi": pts[-1][1], "date": pts[-1][0], "cached": False}


def fetch(lat: float, lon: float) -> dict[str, Any]:
    """Toutes les données réelles disponibles pour le point. Ne lève jamais d'exception."""
    key = f"{round(lat, 2)}:{round(lon, 2)}"
    hit = _CACHE.get(key)
    if hit and time.time() - hit[0] < _TTL:
        return hit[1]

    today = date.today()
    jobs = {
        "power": lambda: _power_daily(lat, lon, today - timedelta(days=62), today),
        "clim": lambda: _power_clim(lat, lon),
        "meteo": lambda: _open_meteo(lat, lon),
        "ndvi": lambda: _ndvi(lat, lon, today),
    }
    raw: dict[str, Any] = {}
    errors: dict[str, str] = {}
    # NDVI : d'abord le cache Neon (permanent), puis le cache mémoire.
    nd_db = _ndvi_db_get(key)
    nd_hit = _NDVI.get(key)
    if nd_db:
        raw["ndvi"] = nd_db
        jobs.pop("ndvi")
    elif nd_hit and time.time() - nd_hit[0] < _NDVI_TTL:
        raw["ndvi"] = nd_hit[1]
        jobs.pop("ndvi")
    futs = {k: _POOL.submit(f) for k, f in jobs.items()}
    if "ndvi" in futs:
        def _keep(fu, k=key):
            if not fu.cancelled() and fu.exception() is None:
                pts = fu.result()
                _NDVI[k] = (time.time(), pts)
                _ndvi_db_put(k, pts)  # persiste pour les prochaines requêtes (toutes instances)
        futs["ndvi"].add_done_callback(_keep)
    deadline = time.time() + 12  # l'analyse n'attend pas plus de ~12 s
    for k, f in futs.items():
        try:
            raw[k] = f.result(timeout=max(0.5, deadline - time.time()))
        except Exception as e:  # réseau, quota, délai, format…
            errors[k] = (type(e).__name__ + ": " + str(e))[:160]
    result = summarize(raw, today)
    result["errors"] = errors
    result["fetched_at"] = datetime.now().isoformat(timespec="minutes")
    if raw:  # on ne garde en cache que si au moins une source a répondu
        _CACHE[key] = (time.time(), result)
    return result


def _days(n: int, end: date) -> list[str]:
    return [(end - timedelta(days=i)).isoformat() for i in range(n - 1, -1, -1)]


def summarize(raw: dict[str, Any], today: date) -> dict[str, Any]:
    """Réduit les réponses brutes en indicateurs utilisables par le moteur."""
    out: dict[str, Any] = {"sources": []}
    power = raw.get("power") or {}
    meteo = raw.get("meteo") or {}
    md = meteo.get("daily") or {}
    m_days = md.get("time") or []
    m_rain = dict(zip(m_days, md.get("precipitation_sum") or []))
    m_et0 = dict(zip(m_days, md.get("et0_fao_evapotranspiration") or []))
    m_temp = dict(zip(m_days, md.get("temperature_2m_mean") or []))
    m_tmax = dict(zip(m_days, md.get("temperature_2m_max") or []))
    m_sw = dict(zip(m_days, md.get("shortwave_radiation_sum") or []))
    if meteo:
        # Open-Meteo travaille en heure locale : « aujourd'hui » au point.
        cur = meteo.get("current") or {}
        local_today = (cur.get("time") or today.isoformat())[:10]
        today = date.fromisoformat(local_today)
    past60 = _days(60, today - timedelta(days=1))

    # --- Pluie des 60 derniers jours : NASA POWER, complétée par Open-Meteo
    p_rain = power.get("PRECTOTCORR") or {}
    rain_days, n_power, last_power = {}, 0, None
    for d in past60:
        if d in p_rain:
            rain_days[d] = p_rain[d]; n_power += 1; last_power = d
        elif m_rain.get(d) is not None:
            rain_days[d] = m_rain[d]
    if len(rain_days) >= 50:
        out["rain_daily"] = rain_days
        out["rainfall_60d_mm"] = round(sum(rain_days.values()))
    if p_rain:
        out["sources"].append({"name": "NASA POWER", "what": "rain_temp_solar_soil", "date": last_power, "live": True})

    # --- Normale climatologique sur la même fenêtre (NASA POWER 1981-2020)
    clim = raw.get("clim")
    if clim:
        normal = sum(clim[MONTHS[date.fromisoformat(d).month - 1]] for d in past60)
        out["rainfall_normal_mm"] = round(normal)
        out["clim_mm_day"] = {m: clim[m] for m in MONTHS}

    # --- Anomalie de température : NASA POWER journalier vs normale NASA POWER (même source)
    t2m = power.get("T2M") or {}
    t_clim = (clim or {}).get("_T2M") or {}
    if t_clim and all(t_clim.get(m, -999) > -900 for m in MONTHS):
        # Température normale par mois (NASA POWER 1981-2020) — sert au moteur pour
        # savoir si la saison est assez chaude pour semer (zones tempérées).
        out["temp_normal_monthly"] = {m: round(t_clim[m], 1) for m in MONTHS}
    if t2m and t_clim:
        last = sorted(t2m)[-14:]  # 14 derniers jours publiés
        diffs = [t2m[d] - t_clim[MONTHS[date.fromisoformat(d).month - 1]] for d in last
                 if t_clim.get(MONTHS[date.fromisoformat(d).month - 1], -999) > -900]
        if diffs:
            out["temp_anomaly"] = round(sum(diffs) / len(diffs), 1)

    # --- Humidité de la zone racinaire NASA POWER (0-1), dernière valeur
    gw = power.get("GWETROOT") or {}
    if gw:
        last = max(gw)
        out["root_zone_wetness"] = round(gw[last], 2)
        out["root_zone_date"] = last

    # --- Météo actuelle et prévision (Open-Meteo)
    if meteo:
        cur = meteo.get("current") or {}
        out["current"] = {
            "time": cur.get("time"), "temperature_c": cur.get("temperature_2m"),
            "wind_speed_kmh": cur.get("wind_speed_10m"), "wind_dir_deg": cur.get("wind_direction_10m"),
            "humidity_pct": cur.get("relative_humidity_2m"), "precip_mm": cur.get("precipitation"),
        }
        fut = [d for d in m_days if d >= today.isoformat()][:16]
        out["forecast"] = [{"date": d, "rain_mm": m_rain.get(d) or 0.0, "et0_mm": m_et0.get(d),
                            "tmax_c": m_tmax.get(d)} for d in fut]
        out["forecast_rain_16d_mm"] = round(sum(f["rain_mm"] for f in out["forecast"]))
        last7 = _days(7, today - timedelta(days=1))
        et = [m_et0[d] for d in last7 if m_et0.get(d) is not None]
        if et:
            out["et0_mm_day"] = round(sum(et) / len(et), 1)
        tm = [m_temp[d] for d in last7 if m_temp.get(d) is not None]
        if tm:
            out["temperature_7d_c"] = round(sum(tm) / len(tm), 1)

        sw = [m_sw[d] for d in last7 if m_sw.get(d) is not None]
        if sw:
            out["solar_mj_m2"] = round(sum(sw) / len(sw), 1)
        hs = meteo.get("hourly") or {}
        sm = [v for v in (hs.get("soil_moisture_9_to_27cm") or []) if v is not None]
        times = hs.get("time") or []
        # dernière valeur passée (pas une prévision)
        now_iso = (cur.get("time") or "")[:13]
        past_sm = [v for t, v in zip(times, hs.get("soil_moisture_9_to_27cm") or []) if v is not None and t[:13] <= now_iso]
        if past_sm or sm:
            out["soil_moisture"] = round((past_sm or sm)[-1], 3)
        soil_day: dict[str, list[float]] = {}
        for t, v in zip(times, hs.get("soil_moisture_9_to_27cm") or []):
            if v is not None and t[:13] <= now_iso:
                soil_day.setdefault(t[:10], []).append(v)
        out["daily"] = {"time": m_days, "rain": m_rain, "et0": m_et0, "temp": m_temp, "solar": m_sw,
                        "soil": {d: round(sum(v) / len(v), 3) for d, v in soil_day.items()}}
        out["today"] = today.isoformat()
        out["sources"].append({"name": "Open-Meteo", "what": "weather_forecast", "date": cur.get("time"), "live": True})

    # --- NDVI MODIS
    nd = raw.get("ndvi") or []
    if nd:
        out["ndvi_points"] = nd
        out["ndvi"] = nd[-1][1]
        prev = [v for _, v in nd[:-1]]
        out["ndvi_trend"] = round(nd[-1][1] - (sum(prev) / len(prev)), 2) if prev else 0.0
        out["sources"].append({"name": "NASA MODIS (MOD13Q1)", "what": "ndvi", "date": nd[-1][0], "live": True})
    return out
