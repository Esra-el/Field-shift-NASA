"""20-year, same-date drought analog on NASA POWER.

The headline NASA-data method for Field Shift: to judge conditions for *today*,
compare the recent weather to the SAME calendar date (±a few days) across the
last ~20 years of NASA POWER daily data for this exact point. The result is a
plain, honest signal — e.g. "rainfall for mid-November is in the driest 15% of
the last 20 years here" — that drives the drought-risk score.

Everything comes from ONE NASA source (POWER, global, 40+ years, no API key), so
the current reading and the 20-year baseline are measured the same way (apples to
apples). Never raises: on any problem it returns {"source": "unavailable"} and
the caller keeps its existing estimate.
"""
from __future__ import annotations

import datetime as _dt

from . import data as power_data  # reuses POWER fetch + on-disk cache

# POWER daily params: rain, temperature, root-zone soil wetness, solar.
PARAMS = "PRECTOTCORR,T2M,GWETROOT,ALLSKY_SFC_SW_DWN"
_FILL = -900.0           # POWER fill value is -999
_LAG_DAYS = 5            # POWER publishes with a short delay
RECENT_DAYS = 60         # the window we accumulate rainfall over
WINDOW_DAYS = 10         # ± this many days around the calendar date = "this time of year"
YEARS = 20


def _level(score: int) -> str:
    return "high" if score >= 70 else "moderate" if score >= 40 else "low"


def _pct_below(sample: list[float], value: float | None) -> float | None:
    """Mid-rank percentile of `value` within the 20-year sample (0..1). Low = unusually
    dry/cold. Mid-rank (ties count half) so a value equal to the norm scores ~0.5."""
    if not sample or value is None:
        return None
    below = sum(1 for s in sample if s < value)
    equal = sum(1 for s in sample if s == value)
    return (below + 0.5 * equal) / len(sample)


def _mmdd_window(center: _dt.date, days: int) -> set[str]:
    return {(center + _dt.timedelta(d)).strftime("%m%d") for d in range(-days, days + 1)}


# The 20-year fetch is the only slow part (~8 s uncached); results are stable for a
# day, so cache per rounded point + date in memory (POWER's raw JSON is also disk-cached).
_MEM: dict[tuple, dict] = {}


def analog(lat: float, lon: float, today: _dt.date | None = None,
           years: int = YEARS, window_days: int = WINDOW_DAYS,
           recent_days: int = RECENT_DAYS) -> dict:
    """Drought-risk signal from the 20-year same-date POWER analog. Never raises."""
    today = today or _dt.date.today()
    key = (round(lat, 2), round(lon, 2), today.isoformat(), years, window_days, recent_days)
    cached = _MEM.get(key)
    if cached is not None:
        return cached
    try:
        result = _analog(lat, lon, today, years, window_days, recent_days)
    except Exception:
        result = {"source": "unavailable"}
    if result.get("source") == "power_analog":  # only cache a real success
        _MEM[key] = result
    return result


def _analog(lat, lon, today, years, window_days, recent_days) -> dict:
    end = today - _dt.timedelta(days=_LAG_DAYS)
    start_year = end.year - years
    power = power_data.fetch_power(lat, lon, f"{start_year}0101", end.strftime("%Y%m%d"))
    param = (power or {}).get("properties", {}).get("parameter", {}) or {}
    rain, t2m, soil = param.get("PRECTOTCORR", {}), param.get("T2M", {}), param.get("GWETROOT", {})
    if not rain:
        return {"source": "unavailable"}

    years_present = sorted({int(k[:4]) for k in rain})
    if len(years_present) < 5:
        return {"source": "unavailable"}
    current_year = years_present[-1]
    hist_years = [y for y in years_present if y < current_year][-years:]
    win = _mmdd_window(today, window_days)

    def rain_accum(year: int, end_date: _dt.date) -> float | None:
        acc, n = 0.0, 0
        for d in range(recent_days):
            v = rain.get((end_date - _dt.timedelta(d)).strftime("%Y%m%d"))
            if v is not None and v > _FILL:
                acc, n = acc + v, n + 1
        return acc if n >= recent_days * 0.6 else None

    def window_mean(series: dict, year: int) -> float | None:
        vals = [series[k] for k in series if k[:4] == str(year) and k[4:] in win and series[k] > _FILL]
        return sum(vals) / len(vals) if vals else None

    # --- current year (the "now" reading), ending at the most recent POWER date ---
    try:
        cur_target = _dt.date(current_year, today.month, today.day)
    except ValueError:
        cur_target = _dt.date(current_year, today.month, 28)
    cur_target = min(cur_target, end)
    cur_rain = rain_accum(current_year, cur_target)
    cur_soil = window_mean(soil, current_year)
    cur_temp = window_mean(t2m, current_year)

    # --- 20-year distributions for the SAME calendar date ---
    rain_hist, soil_hist, temp_hist = [], [], []
    for y in hist_years:
        try:
            tgt = _dt.date(y, today.month, today.day)
        except ValueError:
            tgt = _dt.date(y, today.month, 28)
        r = rain_accum(y, tgt)
        if r is not None:
            rain_hist.append(r)
        s, t = window_mean(soil, y), window_mean(t2m, y)
        if s is not None:
            soil_hist.append(s)
        if t is not None:
            temp_hist.append(t)
    if len(rain_hist) < 5 or cur_rain is None:
        return {"source": "unavailable"}

    rain_pct = _pct_below(rain_hist, cur_rain)            # low = dry
    soil_pct = _pct_below(soil_hist, cur_soil)            # low = dry soil
    temp_pct = _pct_below(temp_hist, cur_temp)            # high = hot

    # Composite drought risk: drier rain & soil and hotter -> higher. Rain weighted most.
    dry_rain = 1.0 - rain_pct
    dry_soil = 1.0 - soil_pct if soil_pct is not None else dry_rain
    hot = temp_pct if temp_pct is not None else 0.5
    score = int(round(max(0.0, min(1.0, 0.55 * dry_rain + 0.30 * dry_soil + 0.15 * hot)) * 100))

    drivers = []
    drivers.append(
        f"rainfall is in the driest {round(dry_rain * 100)}% of the last {len(rain_hist)} years for this date"
        if dry_rain >= 0.5 else
        f"rainfall is near or above the {len(rain_hist)}-year normal for this date"
    )
    if soil_pct is not None and dry_soil >= 0.6:
        drivers.append(f"soil is drier than {round(dry_soil * 100)}% of past years here now")
    if temp_pct is not None and hot >= 0.7:
        drivers.append(f"temperature is warmer than {round(hot * 100)}% of past years for this date")

    median_rain = sorted(rain_hist)[len(rain_hist) // 2]
    return {
        "source": "power_analog",
        "risk_score": score,
        "risk_level": _level(score),
        "rain_percentile": round(rain_pct, 2),
        "rain_recent_mm": round(cur_rain, 1),
        "rain_normal_mm": round(median_rain, 1),
        "soil_percentile": round(soil_pct, 2) if soil_pct is not None else None,
        "temp_percentile": round(temp_pct, 2) if temp_pct is not None else None,
        "drivers": drivers,
        "n_years": len(rain_hist),
        "window_days": window_days,
        "as_of": cur_target.isoformat(),
        "data_mode": "real",
    }
