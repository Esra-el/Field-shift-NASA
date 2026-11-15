"""Field Shift — Moteur MOCK de recommandations (Flux 1), multilingue.

Génère une recommandation plausible au format du contrat d'API (document
d'équipe, section 8.6). Permet au Flux 1 (front/PWA) de travailler sans le
moteur réel de données NASA + ML + IA du Flux 2.

Les textes sont localisés en ES / EN / FR / IT selon le champ `lang` de l'entrée
(défaut : es). Le Flux 2 remplacera ce module par le vrai pipeline en gardant
ce format de sortie.
"""
from __future__ import annotations

import hashlib
import math
from datetime import date, timedelta
from typing import Any

try:  # modèle ML de risque du Flux 2 (backend/app/ml) ; absent -> règles simples
    from app.ml.risk import predict_risk as _predict_risk
except Exception:  # pragma: no cover
    _predict_risk = None

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

# --- Données agronomiques de démonstration (mm/saison approx.) -------------
CROP_WATER_NEED_MM: dict[str, int] = {
    "maize": 520, "beans": 350, "sorghum": 400, "millet": 380, "cover_crop": 300, "other": 450,
}
SOIL_RETENTION: dict[str, float] = {
    "sandy": 0.55, "sandy_loam": 0.75, "loam": 1.0, "clay_loam": 1.15, "clay": 1.25,
}

# --- Textes localisés ------------------------------------------------------
CROP_LABEL = {
    "es": {"maize": "maíz", "beans": "frijol", "sorghum": "sorgo", "millet": "mijo", "cover_crop": "cultivo de cobertura", "other": "otro cultivo"},
    "fr": {"maize": "maïs", "beans": "haricot", "sorghum": "sorgho", "millet": "millet", "cover_crop": "culture de couverture", "other": "autre culture"},
    "en": {"maize": "maize", "beans": "beans", "sorghum": "sorghum", "millet": "millet", "cover_crop": "cover crop", "other": "other crop"},
    "it": {"maize": "mais", "beans": "fagioli", "sorghum": "sorgo", "millet": "miglio", "cover_crop": "coltura di copertura", "other": "altra coltura"},
}
RISK_WORD = {
    "es": {"low": "bajo", "moderate": "moderado", "high": "alto"},
    "fr": {"low": "bas", "moderate": "modéré", "high": "élevé"},
    "en": {"low": "low", "moderate": "moderate", "high": "high"},
    "it": {"low": "basso", "moderate": "moderato", "high": "alto"},
}
WS_WORD = {
    "es": {"enough_water": "agua suficiente", "risky": "agua justa", "not_enough_water": "agua insuficiente"},
    "fr": {"enough_water": "assez d'eau", "risky": "eau juste", "not_enough_water": "eau insuffisante"},
    "en": {"enough_water": "enough water", "risky": "tight water", "not_enough_water": "not enough water"},
    "it": {"enough_water": "acqua sufficiente", "risky": "acqua al limite", "not_enough_water": "acqua insufficiente"},
}
TXT = {
    "es": {
        "reason_season": "Es temporada seca en su parcela. Según la normal de NASA POWER, las lluvias regresan hacia el {date}: prepare el suelo y siembre entonces.",
        "reason_forecast": "Open-Meteo prevé unos {mm} mm de lluvia a partir del {date}: siembre justo después de esa lluvia.",
        "water_expl": "La lluvia y la humedad del suelo cubren cerca del {cov}% de lo que necesita el cultivo.",
        "reason_plant_now": "La humedad del suelo y la lluvia esperada cubren lo que necesita el cultivo. Es un buen momento para sembrar.",
        "reason_wait": "El suelo tiene poca humedad y la lluvia esperada aún no alcanza. Es mejor esperar la próxima ventana de lluvia.",
        "reason_switch": "Falta mucha agua para este cultivo. Considere un cultivo más resistente o una rotación que baje el riesgo.",
        "rot_safest_name": "Frijol → Sorgo → Cobertura",
        "rot_safest_reason": "Depende menos del agua y mantiene el suelo cubierto. El sorgo aguanta la sequía y la cobertura protege el suelo entre temporadas.",
        "rot_balanced_name": "Leguminosa → Cereal → Cobertura/descanso",
        "rot_balanced_reason": "Mantiene la producción y mejora la salud del suelo gracias a las leguminosas que fijan nitrógeno.",
        "rot_yield_name": "Maíz (con alertas de riesgo de agua)",
        "rot_yield_reason": "Da la mayor cosecha cuando hay agua suficiente, pero exige vigilar de cerca la lluvia y la humedad del suelo.",
        "ai": "Su parcela tiene un riesgo de sequía {risk} (puntaje {score}/100). Para el {crop}, la necesidad estimada es de {need} mm y el agua disponible de {avail} mm, es decir {ws}. {tail} Fuentes NASA usadas: GPM IMERG (lluvia), SMAP (humedad), MODIS/VIIRS (NDVI) y NASA POWER (radiación y evapotranspiración).",
        "ai_tail_plant": "Puede sembrar dentro de la ventana recomendada.",
        "ai_tail_other": "Es mejor esperar o considerar una rotación más resistente.",
    },
    "fr": {
        "reason_season": "C'est la saison sèche sur ta parcelle. D'après la normale NASA POWER, les pluies reviennent vers le {date} : prépare le sol et sème à ce moment-là.",
        "reason_forecast": "Open-Meteo prévoit environ {mm} mm de pluie à partir du {date} : sème juste après cette pluie.",
        "water_expl": "La pluie et l'humidité du sol couvrent environ {cov}% du besoin estimé de la culture.",
        "reason_plant_now": "L'humidité du sol et la pluie attendue couvrent le besoin de la culture. Les conditions sont favorables au semis.",
        "reason_wait": "L'humidité du sol est limitée et la pluie attendue encore insuffisante. Mieux vaut attendre la prochaine fenêtre de pluie.",
        "reason_switch": "Le déficit d'eau est élevé pour cette culture. Envisage une culture plus résistante ou une rotation qui réduit le risque.",
        "rot_safest_name": "Haricot → Sorgho → Couverture",
        "rot_safest_reason": "Réduit la dépendance à l'eau et garde le sol couvert. Le sorgho tolère la sécheresse et la couverture protège le sol entre deux saisons.",
        "rot_balanced_name": "Légumineuse → Céréale → Couverture/jachère",
        "rot_balanced_reason": "Maintient la production et améliore la santé du sol grâce à la rotation avec des légumineuses fixatrices d'azote.",
        "rot_yield_name": "Maïs (avec alertes de risque hydrique)",
        "rot_yield_reason": "Maximise le rendement quand il y a assez d'eau, mais exige de surveiller de près la pluie et l'humidité du sol.",
        "ai": "Ton champ présente un risque de sécheresse {risk} (score {score}/100). Pour le {crop}, le besoin estimé est de {need} mm et l'eau disponible de {avail} mm, soit {ws}. {tail} Sources NASA utilisées : GPM IMERG (pluie), SMAP (humidité), MODIS/VIIRS (NDVI) et NASA POWER (rayonnement et évapotranspiration).",
        "ai_tail_plant": "Tu peux semer dans la fenêtre recommandée.",
        "ai_tail_other": "Mieux vaut attendre ou envisager une rotation plus résistante.",
    },
    "en": {
        "reason_season": "It is the dry season at your field. According to the NASA POWER normal, rains return around {date}: prepare the soil and plant then.",
        "reason_forecast": "Open-Meteo forecasts about {mm} mm of rain from {date}: plant right after that rain.",
        "water_expl": "Rainfall and soil moisture cover about {cov}% of the crop's estimated need.",
        "reason_plant_now": "Soil moisture and expected rainfall cover the crop's need. Conditions are suitable for planting.",
        "reason_wait": "Soil moisture is limited and expected rainfall still insufficient. Better wait for the next rain window.",
        "reason_switch": "The water deficit is high for this crop. Consider a more resilient crop or a rotation that lowers the risk.",
        "rot_safest_name": "Beans → Sorghum → Cover crop",
        "rot_safest_reason": "Cuts water dependence and keeps the soil covered. Sorghum tolerates drought and the cover crop protects the soil between seasons.",
        "rot_balanced_name": "Legume → Cereal → Cover/fallow",
        "rot_balanced_reason": "Maintains production and improves soil health through rotation with nitrogen-fixing legumes.",
        "rot_yield_name": "Maize (with water-risk alerts)",
        "rot_yield_reason": "Maximizes yield when there is enough water, but requires close watch on rainfall and soil moisture.",
        "ai": "Your field has {risk} drought risk (score {score}/100). For {crop}, the estimated need is {need} mm and available water {avail} mm, i.e. {ws}. {tail} NASA sources used: GPM IMERG (rain), SMAP (moisture), MODIS/VIIRS (NDVI) and NASA POWER (radiation and evapotranspiration).",
        "ai_tail_plant": "You can plant within the recommended window.",
        "ai_tail_other": "Better wait or consider a more resilient rotation.",
    },
    "it": {
        "reason_season": "È la stagione secca sul tuo campo. Secondo la normale NASA POWER, le piogge tornano verso il {date}: prepara il suolo e semina allora.",
        "reason_forecast": "Open-Meteo prevede circa {mm} mm di pioggia dal {date}: semina subito dopo quella pioggia.",
        "water_expl": "Pioggia e umidità del suolo coprono circa il {cov}% del fabbisogno stimato della coltura.",
        "reason_plant_now": "L'umidità del suolo e la pioggia attesa coprono il fabbisogno della coltura. Le condizioni sono adatte alla semina.",
        "reason_wait": "L'umidità del suolo è limitata e la pioggia attesa ancora insufficiente. Meglio aspettare la prossima finestra di pioggia.",
        "reason_switch": "Il deficit idrico è elevato per questa coltura. Valuta una coltura più resistente o una rotazione che riduca il rischio.",
        "rot_safest_name": "Fagioli → Sorgo → Copertura",
        "rot_safest_reason": "Riduce la dipendenza dall'acqua e mantiene il suolo coperto. Il sorgo tollera la siccità e la copertura protegge il suolo tra le stagioni.",
        "rot_balanced_name": "Legume → Cereale → Copertura/maggese",
        "rot_balanced_reason": "Mantiene la produzione e migliora la salute del suolo grazie alla rotazione con legumi azotofissatori.",
        "rot_yield_name": "Mais (con avvisi di rischio idrico)",
        "rot_yield_reason": "Massimizza la resa quando c'è abbastanza acqua, ma richiede di monitorare da vicino pioggia e umidità del suolo.",
        "ai": "Il tuo campo ha un rischio di siccità {risk} (punteggio {score}/100). Per il {crop}, il fabbisogno stimato è {need} mm e l'acqua disponibile {avail} mm, cioè {ws}. {tail} Fonti NASA usate: GPM IMERG (pioggia), SMAP (umidità), MODIS/VIIRS (NDVI) e NASA POWER (radiazione ed evapotraspirazione).",
        "ai_tail_plant": "Puoi seminare nella finestra consigliata.",
        "ai_tail_other": "Meglio aspettare o valutare una rotazione più resistente.",
    },
}


def _L(lang: str) -> str:
    return lang if lang in TXT and lang != "es" else "fr"


ROT_ACTIONS = {
    "es": {
        "safest": ["Prepare el suelo y siembre frijol al inicio de la ventana.", "Deje rastrojo o cobertura sobre el suelo.", "Guarde semilla de sorgo para la segunda siembra."],
        "balanced": ["Siembre la leguminosa primero para nutrir el suelo.", "Siembre el cereal cuando la humedad del suelo pase de 20 %.", "Planee una cobertura o un descanso al final."],
        "highest_yield": ["Siembre maíz solo si la lluvia llega en la ventana.", "Revise la humedad del suelo cada semana.", "Tenga un plan B con sorgo si la lluvia falla."],
    },
    "en": {
        "safest": ["Prepare the soil and sow beans at the start of the window.", "Leave residue or cover on the soil.", "Keep sorghum seed for the second planting."],
        "balanced": ["Sow the legume first to feed the soil.", "Sow the cereal once soil moisture passes 20%.", "Plan a cover crop or fallow at the end."],
        "highest_yield": ["Plant maize only if rain arrives within the window.", "Check soil moisture every week.", "Keep a plan B with sorghum if the rain fails."],
    },
    "fr": {
        "safest": ["Préparer le sol et semer le haricot au début de la fenêtre.", "Laisser des résidus ou une couverture sur le sol.", "Garder de la semence de sorgho pour le 2e semis."],
        "balanced": ["Semer d'abord la légumineuse pour nourrir le sol.", "Semer la céréale quand l'humidité du sol dépasse 20 %.", "Prévoir une couverture ou une jachère à la fin."],
        "highest_yield": ["Semer le maïs seulement si la pluie arrive dans la fenêtre.", "Vérifier l'humidité du sol chaque semaine.", "Garder un plan B avec du sorgho si la pluie manque."],
    },
    "it": {
        "safest": ["Preparare il suolo e seminare i fagioli all'inizio della finestra.", "Lasciare residui o copertura sul suolo.", "Tenere semi di sorgo per la seconda semina."],
        "balanced": ["Seminare prima il legume per nutrire il suolo.", "Seminare il cereale quando l'umidità del suolo supera il 20%.", "Prevedere una copertura o un maggese alla fine."],
        "highest_yield": ["Seminare mais solo se la pioggia arriva nella finestra.", "Controllare l'umidità del suolo ogni settimana.", "Tenere un piano B con sorgo se la pioggia manca."],
    },
}
CROP_CYCLE = {  # (fin croissance, fin floraison, récolte) en jours après le semis
    "maize": (55, 85, 120), "beans": (35, 55, 85), "sorghum": (50, 80, 110),
    "millet": (40, 65, 95), "cover_crop": (40, 60, 90), "other": (50, 80, 110),
}
IRRIGATION_MM = {"none": 0, "limited": 60, "available": 120}


def _seed(latitude: float, longitude: float) -> float:
    key = f"{round(latitude, 3)}:{round(longitude, 3)}"
    return int(hashlib.sha256(key.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def _risk_level(score: int) -> str:
    if score >= 70:
        return "high"
    if score >= 40:
        return "moderate"
    return "low"


def _first(*vals):
    for v in vals:
        if v is not None:
            return v
    return None


def _clim_rain(clim: dict[str, float], start: date, days: int) -> float:
    """Pluie normale (NASA POWER 1981-2020) cumulée sur `days` jours à partir de `start`."""
    return sum(clim[MONTHS[(start + timedelta(days=i)).month - 1]] for i in range(days))


def _onset(clim: dict[str, float], today: date) -> date:
    """Premier jour, à partir d'aujourd'hui, d'un mois où il pleut ≥ 3 mm/jour en moyenne."""
    for k in range(0, 13):
        y, m = divmod(today.month - 1 + k, 12)
        if clim[MONTHS[m]] >= 3.0:
            return today if k == 0 else date(today.year + y, m + 1, 1)
    return today


def _planting_window(live: dict[str, Any], today: date) -> tuple[date, str]:
    """Fenêtre de semis réelle : sol déjà humide, pluie prévue (Open-Meteo), sinon début de saison des pluies."""
    fc = live.get("forecast") or []
    if (live.get("soil_moisture") or 0) >= 0.26 and sum(f["rain_mm"] for f in fc[:7]) >= 8:
        return today + timedelta(days=1), "now"
    for i in range(len(fc) - 2):
        if sum(f["rain_mm"] for f in fc[i:i + 3]) >= 15:
            return date.fromisoformat(fc[i]["date"]), "forecast"
    clim = live.get("clim_mm_day")
    if clim:
        start = _onset(clim, today + timedelta(days=16))
        return max(start, today + timedelta(days=16)), "season"
    return today + timedelta(days=6), "default"


def generate_recommendation(payload: dict[str, Any], live: dict[str, Any] | None = None) -> dict[str, Any]:
    live = live or {}
    lang = _L(str(payload.get("lang", "fr")))
    T = TXT[lang]

    latitude = float(payload.get("latitude", 14.8))
    longitude = float(payload.get("longitude", -90.5))
    crop = str(payload.get("crop", "maize"))
    soil_type = str(payload.get("soil_type", "sandy_loam"))
    irrigation_level = str(payload.get("irrigation_level") or ("available" if payload.get("irrigation") else "none"))
    if irrigation_level not in IRRIGATION_MM:
        irrigation_level = "none"
    priority = str(payload.get("priority", "balanced"))

    s = _seed(latitude, longitude)

    today = date.fromisoformat(live["today"]) if live.get("today") else date.today()
    is_live = bool(live.get("rainfall_60d_mm") is not None and live.get("clim_mm_day"))
    estimated: list[str] = []  # indicateurs qu'aucune source n'a pu donner

    def pick(key, sim):
        v = live.get(key)
        if v is None:
            estimated.append(key)
            return sim
        return v

    # Indicateurs : données réelles (NASA POWER, MODIS, Open-Meteo) ; estimation seulement en secours
    rainfall_normal = pick("rainfall_normal_mm", round(160 + s * 120))
    rainfall_60d = pick("rainfall_60d_mm", round(rainfall_normal * (0.35 + s * 0.6)))
    soil_moisture = pick("soil_moisture", round(0.08 + s * 0.22, 2))
    ndvi_trend = pick("ndvi_trend", round(-0.20 + s * 0.28, 2))
    solar_radiation = pick("solar_mj_m2", round(18.0 + s * 8.0, 1))
    evapotranspiration = pick("et0_mm_day", round(3.8 + s * 2.2, 1))

    # Fenêtre de semis (calculée avant le budget : l'eau attendue dépend de la date de semis)
    g, f, h = CROP_CYCLE.get(crop, CROP_CYCLE["other"])
    if is_live:
        window_start, window_kind = _planting_window(live, today)
    else:
        window_start, window_kind = today + timedelta(days=6), "default"
    window_end = window_start + timedelta(days=10)

    # Budget d'eau
    retention = SOIL_RETENTION.get(soil_type, 1.0)
    irrigation_mm = IRRIGATION_MM[irrigation_level]
    if is_live:
        # Pluie attendue sur le cycle : prévision Open-Meteo (16 j), puis normale NASA POWER.
        fc = {x["date"]: x["rain_mm"] for x in live.get("forecast") or []}
        clim = live["clim_mm_day"]
        cycle_rain = 0.0
        for i in range(h):
            d = window_start + timedelta(days=i)
            cycle_rain += fc.get(d.isoformat(), clim[MONTHS[d.month - 1]])
        expected_rain = round(cycle_rain * 0.75)               # pluie efficace (~75 %)
        soil_contrib = round(soil_moisture * 600 * retention * 0.5)  # réserve sur 60 cm de racines
        available_water = round(expected_rain + soil_contrib + irrigation_mm)
    else:
        expected_rain = round(rainfall_normal * (0.25 + s * 0.2))
        soil_contrib = round(soil_moisture * 1000 * retention * 0.4)
        available_water = round(rainfall_60d * 0.6 + expected_rain + soil_contrib + irrigation_mm)
    crop_water_need = round(CROP_WATER_NEED_MM.get(crop, 450) * (0.9 + evapotranspiration / 20))
    deficit = max(0, crop_water_need - available_water)
    coverage = min(1.0, available_water / crop_water_need)

    if deficit <= 0:
        water_status = "enough_water"
    elif deficit < 0.35 * crop_water_need:
        water_status = "risky"
    else:
        water_status = "not_enough_water"

    # Score de risque
    risk_score = int(max(0, min(100, 18 + (1 - coverage) * 55 + (1.25 - retention) * 18
                   + max(0, -ndvi_trend) * 60 - irrigation_mm / 12)))
    if is_live and rainfall_normal:
        # Pluie des 60 derniers jours en dessous de la normale NASA : risque en plus
        risk_score = int(max(0, min(100, risk_score + max(0.0, 1 - rainfall_60d / rainfall_normal) * 15)))
    risk_model, risk_confidence = "rules", None
    if is_live and _predict_risk is not None:
        # Score de risque du modèle ML du Flux 2, nourri avec les mesures en direct.
        try:
            ml = _predict_risk({
                "rainfall_anomaly": round((rainfall_60d - rainfall_normal) / rainfall_normal, 3) if rainfall_normal else 0.0,
                "soil_moisture": soil_moisture,
                "ndvi_trend": ndvi_trend,
                "et": evapotranspiration,
                "temp_anomaly": live.get("temp_anomaly", 0.0),
                "solar_radiation": solar_radiation,
            })
            # L'irrigation ne change pas le climat mais réduit le risque pour la culture.
            risk_score = int(max(0, min(100, int(ml["risk_score"]) - irrigation_mm / 12)))
            risk_model = "ml"
            risk_confidence = ml.get("confidence")
        except Exception:
            pass
    risk_level = _risk_level(risk_score)

    # Recommandation de semis
    if window_kind == "season":
        # Saison sèche : la vraie décision est d'attendre le retour des pluies.
        planting_reco = "wait"
        planting_reason = T["reason_season"].format(date=window_start.strftime("%d/%m/%Y"))
    elif risk_level == "high":
        planting_reco, planting_reason = "switch_crop", T["reason_switch"]
    elif window_kind == "forecast" and window_start > today + timedelta(days=2):
        rain3 = round(sum(x["rain_mm"] for x in live["forecast"] if window_start.isoformat() <= x["date"]
                          <= (window_start + timedelta(days=2)).isoformat()))
        planting_reco = "wait"
        planting_reason = T["reason_forecast"].format(mm=rain3, date=window_start.strftime("%d/%m"))
    elif risk_level == "low":
        planting_reco, planting_reason = "plant_now", T["reason_plant_now"]
    else:
        planting_reco, planting_reason = "wait", T["reason_wait"]

    # Rotations
    rotations = [
        {"type": "safest", "name": T["rot_safest_name"], "water_saving": "high", "water_saving_pct": 35,
         "soil_benefit": "high", "yield_potential": "medium", "risk": "low", "reason": T["rot_safest_reason"],
         "actions": ROT_ACTIONS[lang]["safest"]},
        {"type": "balanced", "name": T["rot_balanced_name"], "water_saving": "medium", "water_saving_pct": 20,
         "soil_benefit": "high", "yield_potential": "medium", "risk": "moderate", "reason": T["rot_balanced_reason"],
         "actions": ROT_ACTIONS[lang]["balanced"]},
        {"type": "highest_yield", "name": T["rot_yield_name"], "water_saving": "low", "water_saving_pct": 5,
         "soil_benefit": "medium", "yield_potential": "high", "risk": "high" if risk_level == "high" else "moderate",
         "reason": T["rot_yield_reason"], "actions": ROT_ACTIONS[lang]["highest_yield"]},
    ]
    if priority == "save_water":
        rotations.sort(key=lambda r: {"high": 0, "medium": 1, "low": 2}[r["water_saving"]])
    elif priority == "max_yield":
        rotations.sort(key=lambda r: 0 if r["type"] == "highest_yield" else 1)
    elif priority == "protect_soil":
        rotations.sort(key=lambda r: ({"high": 0, "medium": 1, "low": 2}[r["soil_benefit"]], r["type"] != "safest"))
    elif priority == "food_security":
        rotations.sort(key=lambda r: {"balanced": 0, "safest": 1, "highest_yield": 2}[r["type"]])

    # Explication IA
    ai_explanation = T["ai"].format(
        risk=RISK_WORD[lang][risk_level], score=risk_score,
        crop=CROP_LABEL[lang].get(crop, crop), need=crop_water_need, avail=available_water,
        ws=WS_WORD[lang][water_status],
        tail=T["ai_tail_plant"] if planting_reco == "plant_now" else T["ai_tail_other"],
    )

    # Vent et chaleur : météo actuelle Open-Meteo (estimation seulement en secours)
    cur = live.get("current") or {}
    wind_speed = _first(cur.get("wind_speed_kmh"), round(6 + s * 16, 1))
    wind_dir = int(_first(cur.get("wind_dir_deg"), (40 + s * 280) % 360))
    if not cur:
        estimated.append("wind")
    temperature_c = _first(live.get("temperature_7d_c"), round(24 + s * 6, 1))
    tmax_fc = max([x["tmax_c"] for x in live.get("forecast") or [] if x.get("tmax_c") is not None] or [0])

    # Calendrier de saison : stades de la culture + épisodes secs
    sow = window_start
    harvest_end = sow + timedelta(days=h)
    dry_spells: list[dict[str, Any]] = []
    if is_live:
        # 1) épisodes secs prévus par Open-Meteo : au moins 5 jours de suite avec < 1 mm
        run: list[str] = []
        for x in (live.get("forecast") or []) + [{"date": "9999-12-31", "rain_mm": 99}]:
            if x["rain_mm"] < 1:
                run.append(x["date"])
                continue
            if len(run) >= 5 and run[-1] >= sow.isoformat() and run[0] <= harvest_end.isoformat():
                dry_spells.append({"start": run[0], "end": run[-1],
                                   "level": "high" if len(run) >= 10 else "moderate", "source": "forecast"})
            run = []
        # 2) mois secs du cycle selon la normale NASA POWER (ex. la canícula de juillet)
        clim = live["clim_mm_day"]
        months: list[tuple[int, int, float]] = []
        d = sow
        while d <= harvest_end:
            if not months or months[-1][:2] != (d.year, d.month):
                months.append((d.year, d.month, clim[MONTHS[d.month - 1]]))
            d += timedelta(days=1)
        avg = sum(v for _, _, v in months) / max(1, len(months))
        for y, m, v in months:
            if v < 0.7 * avg or v < 2.0:
                a = max(sow, date(y, m, 1))
                b = min(harvest_end, date(y + m // 12, m % 12 + 1, 1) - timedelta(days=1))
                if a < b:
                    dry_spells.append({"start": a.isoformat(), "end": b.isoformat(),
                                       "level": "high" if v < 1.5 else "moderate", "source": "normal"})
    elif risk_level != "low":
        dry_spells = [{"start": (sow + timedelta(days=int(30 + s * 20))).isoformat(),
                       "end": (sow + timedelta(days=int(30 + s * 20) + (14 if risk_level == "moderate" else 24))).isoformat(),
                       "level": risk_level}]
    season = {
        "stages": [
            {"stage": "planting", "start": window_start.isoformat(), "end": window_end.isoformat()},
            {"stage": "growing", "start": (sow + timedelta(days=11)).isoformat(), "end": (sow + timedelta(days=g)).isoformat()},
            {"stage": "flowering", "start": (sow + timedelta(days=g)).isoformat(), "end": (sow + timedelta(days=f)).isoformat()},
            {"stage": "harvest", "start": (sow + timedelta(days=f + 15)).isoformat(), "end": harvest_end.isoformat()},
        ],
        "dry_spells": dry_spells,
    }

    # Une seule priorité pour la semaine (clé traduite côté interface)
    if planting_reco == "switch_crop":
        week_focus = "resilient_rotation"
    elif soil_moisture < 0.15:
        week_focus = "soil_cover"
    elif planting_reco == "wait":
        week_focus = "monitor_rain"
    else:
        week_focus = "prepare_planting"

    # Séries temporelles (8 semaines) pour les graphiques
    n = 8
    labels = [(today - timedelta(weeks=(n - 1 - i))).strftime("%d/%m") for i in range(n)]

    def _serie(base, amp, ndigits=2):
        vals = [round(base + math.sin(i * 0.8 + s * 6.283) * amp, ndigits) for i in range(n)]
        vals[-1] = round(base, ndigits)
        return vals

    daily = live.get("daily") or {}

    def _week_end(i: int) -> date:
        return today - timedelta(days=1) - timedelta(weeks=(n - 1 - i))

    def _weekly(src, agg: str, ndigits: int):
        """Valeurs réelles par semaine (somme ou moyenne) ; None si trop peu de jours."""
        if not src:
            return None
        out = []
        for i in range(n):
            vals = [src.get((_week_end(i) - timedelta(days=k)).isoformat()) for k in range(7)]
            vals = [v for v in vals if v is not None]
            if len(vals) < 4:
                return None
            out.append(round(sum(vals) if agg == "sum" else sum(vals) / len(vals), ndigits))
        return out

    clim = live.get("clim_mm_day")
    rain_w = _weekly(live.get("rain_daily"), "sum", 0)
    if clim:
        norm_w = [round(sum(clim[MONTHS[(_week_end(i) - timedelta(days=k)).month - 1]] for k in range(7)))
                  for i in range(n)]
    else:
        norm_w = [max(1, round(rainfall_normal / n))] * n
    ndvi_pts = live.get("ndvi_points") or []

    def _ndvi_at(d: date) -> float:
        return min(ndvi_pts, key=lambda p: abs((date.fromisoformat(p[0]) - d).days))[1]

    rain_week = max(1, round(rainfall_60d / n))
    series = {
        "labels": labels,
        "rainfall_mm": [int(v) for v in rain_w] if rain_w
                       else [max(0, int(v)) for v in _serie(rain_week, rain_week * 0.6, 0)],
        "rainfall_normal_mm": norm_w,
        "soil_moisture": _weekly(daily.get("soil"), "mean", 3) or [max(0.02, v) for v in _serie(soil_moisture, 0.03)],
        "ndvi": [_ndvi_at(_week_end(i)) for i in range(n)] if ndvi_pts
                else [min(0.9, max(0.1, v)) for v in _serie(0.55 + ndvi_trend, 0.05)],
        "temperature_c": _weekly(daily.get("temp"), "mean", 1) or _serie(temperature_c, 2.0, 1),
        "solar_radiation": _weekly(daily.get("solar"), "mean", 1) or _serie(solar_radiation, 2.0, 1),
        "evapotranspiration": _weekly(daily.get("et0"), "mean", 1)
                              or [max(1.0, v) for v in _serie(evapotranspiration, 0.6, 1)],
    }

    # Décomposition du risque (chaque composante : valeur, niveau, source, poids).
    rc_rain = "bad" if rainfall_60d < 0.7 * rainfall_normal else "warn" if rainfall_60d < 0.9 * rainfall_normal else "ok"
    rc_soil = "bad" if soil_moisture < 0.12 else "warn" if soil_moisture < 0.2 else "ok"
    rc_ndvi = "bad" if ndvi_trend < -0.1 else "warn" if ndvi_trend < 0 else "ok"
    rc_heat = "bad" if evapotranspiration > 5.5 else "warn" if evapotranspiration > 4.5 else "ok"
    ndvi_now = live.get("ndvi")
    ndvi_txt = f"{ndvi_trend:+}" + (f" (NDVI {ndvi_now})" if ndvi_now is not None else "")

    def _src(key: str, name: str) -> str:
        return "estimation" if key in estimated else name

    risk_components = [
        {"factor": "rainfall", "value": f"{rainfall_60d}/{rainfall_normal} mm", "level": rc_rain,
         "source": _src("rainfall_60d_mm", "NASA POWER"), "weight": "35%"},
        {"factor": "soil_moisture", "value": f"{soil_moisture} m³/m³", "level": rc_soil,
         "source": _src("soil_moisture", "Open-Meteo"), "weight": "25%"},
        {"factor": "ndvi", "value": ndvi_txt, "level": rc_ndvi,
         "source": _src("ndvi_trend", "NASA MODIS"), "weight": "20%"},
        {"factor": "heat", "value": f"{evapotranspiration} mm/j · {temperature_c}°C", "level": rc_heat,
         "source": _src("et0_mm_day", "Open-Meteo ET₀"), "weight": "20%"},
    ]

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "water_budget": {
            "status": water_status,
            "crop_water_need_mm": crop_water_need,
            "available_water_mm": available_water,
            "deficit_mm": deficit,
            "coverage_pct": round(coverage * 100),
            "expected_rain_mm": expected_rain,
            "soil_water_mm": soil_contrib,
            "irrigation_mm": irrigation_mm,
            "explanation": T["water_expl"].format(cov=round(coverage * 100)),
        },
        "planting_timeline": {
            "recommendation": planting_reco,
            "best_window": f"{window_start.isoformat()} → {window_end.isoformat()}",
            "reason": planting_reason,
            "basis": window_kind,
        },
        "rotations": rotations,
        "irrigation_level": irrigation_level,
        "nasa_indicators": {
            "rainfall_60d_mm": rainfall_60d, "rainfall_normal_mm": rainfall_normal,
            "soil_moisture": soil_moisture, "ndvi_trend": ndvi_trend,
            "solar_radiation": solar_radiation, "evapotranspiration": evapotranspiration,
            "temperature_c": temperature_c,
            "ndvi": ndvi_now, "root_zone_wetness": live.get("root_zone_wetness"),
            "forecast_rain_16d_mm": live.get("forecast_rain_16d_mm"),
        },
        "ai_explanation": ai_explanation,
        "series": series,
        "risk_components": risk_components,
        "weather": {
            "wind_speed_kmh": wind_speed, "wind_dir_deg": wind_dir,
            "temperature_c": _first(cur.get("temperature_c"), temperature_c),
            "humidity_pct": cur.get("humidity_pct"), "observed_at": cur.get("time"),
            "heat_stress": temperature_c >= 29 or evapotranspiration > 5.5 or tmax_fc >= 36,
        },
        "forecast": live.get("forecast") or [],
        "season": season,
        "week_focus": week_focus,
        "data_sources": live.get("sources") or [],
        # Pluie normale par mois (NASA POWER 1981-2020), en mm/mois — pour la page Saison
        "rain_normal_monthly": ({m: round(v * 30.4) for m, v in live["clim_mm_day"].items()}
                                if live.get("clim_mm_day") else None),
        "estimated": estimated,
        "live": is_live,
        "data_mode": "real" if is_live else "mock",
        "risk_model": risk_model,
        "risk_confidence": risk_confidence if risk_model == "ml" else None,
        "fetched_at": live.get("fetched_at"),
        "live_errors": live.get("errors") or {},
        "_mock": not is_live,
    }


# --- Copilote (mock, orienté par l'intention de la question) ---------------
INTENT_KW = {
    "soil": ["suelo", "soil", "protej", "proteg", "protect", "suolo", "le sol", "mon sol"],
    "water": ["eau", "agua", "acqua", "water", "assez", "enough", "suffis", "suffic"],
    "timing": ["quand", "when", "quando", "cuándo", "cuando", "semer", "sembrar", "sow", "plant", "semin", "date", "moment", "fecha"],
    "rotation": ["rotation", "rotación", "rotacion", "rotazione", "culture", "cultivo", "coltura", "crop", "cambiar", "variété", "variete"],
    "irrigation": ["irrig", "riego", "arros"],
}
COPILOT = {
    "es": {
        "ack": "Buena pregunta.",
        "risk": {"low": "El riesgo de sequía es bajo.", "moderate": "El riesgo de sequía es moderado.", "high": "El riesgo de sequía es alto."},
        "the_crop": "su cultivo",
        "water_head": "Sobre el agua: tiene {avail} mm disponibles y {crop} necesita {need} mm.",
        "w_enough": "Alcanza para sembrar.",
        "w_risky": "Está justo: siembre menos denso o elija un cultivo que pida menos agua.",
        "w_not": "Faltan {deficit} mm: es mejor esperar la lluvia o cambiar de cultivo.",
        "timing": {"plant_now": "Puede sembrar ahora.", "wait": "Es mejor esperar.", "switch_crop": "Mejor cambie de cultivo o de rotación."},
        "timing_window": "Ventana recomendada: {window}.",
        "rotation": "La rotación más segura aquí: {rot0}. Ahorra agua y protege el suelo.",
        "irrigation": "Sin riego, todo depende de la lluvia y de la humedad del suelo. {wline} El frijol o el sorgo piden menos agua que el maíz.",
        "soil": "Para proteger el suelo: no lo deje desnudo, deje rastrojo, siembre una cobertura entre temporadas y alterne leguminosas con cereales.",
        "alternatives": "Cultivos que piden menos agua: frijol, sorgo o mijo.",
        "actions": ["Revise la humedad del suelo antes de sembrar.", "Deje rastrojo o cobertura sobre el suelo.", "Hable con su cooperativa antes de comprar semilla."],
        "h": {"reco": "Recomendación", "water": "Agua", "alt": "Cultivos alternativos", "actions": "Qué hacer ahora", "sources": "Fuentes NASA", "limits": "Límites"},
        "tail": "(Datos NASA: GPM, SMAP, MODIS, POWER. Estimación con límites — confirme con su cooperativa.)",
        "limit": "Respuesta de demostración: es una estimación a partir de datos satelitales y no reemplaza la visita de un técnico.",
    },
    "fr": {
        "ack": "Bonne question.",
        "risk": {"low": "Le risque de sécheresse est bas.", "moderate": "Le risque de sécheresse est modéré.", "high": "Le risque de sécheresse est élevé."},
        "the_crop": "ta culture",
        "water_head": "Côté eau : tu as {avail} mm disponibles et {crop} a besoin de {need} mm.",
        "w_enough": "C'est suffisant pour semer.",
        "w_risky": "C'est juste — réduis la densité ou choisis une culture moins gourmande.",
        "w_not": "Il manque {deficit} mm : mieux vaut attendre la pluie ou changer de culture.",
        "timing": {"plant_now": "Tu peux semer maintenant.", "wait": "Mieux vaut attendre.", "switch_crop": "Change plutôt de culture ou de rotation."},
        "timing_window": "Fenêtre conseillée : {window}.",
        "rotation": "La rotation la plus sûre ici : {rot0}. Elle économise l'eau et protège le sol.",
        "irrigation": "Sans irrigation, tout repose sur la pluie et l'humidité du sol. {wline} Le haricot ou le sorgho demandent moins d'eau que le maïs.",
        "soil": "Pour protéger le sol : ne le laisse pas nu, garde les résidus, sème une couverture entre deux saisons et alterne légumineuses et céréales.",
        "alternatives": "Cultures moins gourmandes en eau : haricot, sorgho ou millet.",
        "actions": ["Vérifie l'humidité du sol avant de semer.", "Laisse des résidus ou une couverture sur le sol.", "Parle avec ta coopérative avant d'acheter la semence."],
        "h": {"reco": "Recommandation", "water": "Eau", "alt": "Cultures alternatives", "actions": "Que faire maintenant", "sources": "Sources NASA", "limits": "Limites"},
        "tail": "(Données NASA : GPM, SMAP, MODIS, POWER. Estimation avec limites — valide avec ta coopérative.)",
        "limit": "Réponse de démonstration. Le vrai copilote (Claude API) sera branché par le flux 2.",
    },
    "en": {
        "ack": "Good question.",
        "risk": {"low": "Drought risk is low.", "moderate": "Drought risk is moderate.", "high": "Drought risk is high."},
        "the_crop": "your crop",
        "water_head": "On water: you have {avail} mm available and {crop} needs {need} mm.",
        "w_enough": "That's enough to plant.",
        "w_risky": "It's tight — lower density or pick a less thirsty crop.",
        "w_not": "You're short {deficit} mm: better wait for rain or switch crop.",
        "timing": {"plant_now": "You can plant now.", "wait": "Better wait.", "switch_crop": "Rather switch crop or rotation."},
        "timing_window": "Recommended window: {window}.",
        "rotation": "The safest rotation here: {rot0}. It saves water and protects the soil.",
        "irrigation": "Without irrigation, everything depends on rain and soil moisture. {wline} Beans or sorghum need less water than maize.",
        "soil": "To protect your soil: never leave it bare, keep crop residue, sow a cover crop between seasons and alternate legumes with cereals.",
        "alternatives": "Crops that need less water: beans, sorghum or millet.",
        "actions": ["Check soil moisture before planting.", "Leave residue or cover on the soil.", "Talk to your cooperative before buying seed."],
        "h": {"reco": "Recommendation", "water": "Water", "alt": "Alternative crops", "actions": "What to do now", "sources": "NASA sources", "limits": "Limitations"},
        "tail": "(NASA data: GPM, SMAP, MODIS, POWER. Estimate with limits — confirm with your cooperative.)",
        "limit": "Demo answer. The real copilot (Claude API) will be wired by Flux 2.",
    },
    "it": {
        "ack": "Buona domanda.",
        "risk": {"low": "Il rischio di siccità è basso.", "moderate": "Il rischio di siccità è moderato.", "high": "Il rischio di siccità è alto."},
        "the_crop": "la tua coltura",
        "water_head": "Sull'acqua: hai {avail} mm disponibili e {crop} ha bisogno di {need} mm.",
        "w_enough": "È sufficiente per seminare.",
        "w_risky": "È al limite — riduci la densità o scegli una coltura meno esigente.",
        "w_not": "Mancano {deficit} mm: meglio aspettare la pioggia o cambiare coltura.",
        "timing": {"plant_now": "Puoi seminare ora.", "wait": "Meglio aspettare.", "switch_crop": "Meglio cambiare coltura o rotazione."},
        "timing_window": "Finestra consigliata: {window}.",
        "rotation": "La rotazione più sicura qui: {rot0}. Risparmia acqua e protegge il suolo.",
        "irrigation": "Senza irrigazione, tutto dipende da pioggia e umidità del suolo. {wline} Fagioli o sorgo richiedono meno acqua del mais.",
        "soil": "Per proteggere il suolo: non lasciarlo nudo, tieni i residui, semina una copertura tra le stagioni e alterna legumi e cereali.",
        "alternatives": "Colture che richiedono meno acqua: fagioli, sorgo o miglio.",
        "actions": ["Controlla l'umidità del suolo prima di seminare.", "Lascia residui o copertura sul suolo.", "Parla con la cooperativa prima di comprare il seme."],
        "h": {"reco": "Raccomandazione", "water": "Acqua", "alt": "Colture alternative", "actions": "Cosa fare ora", "sources": "Fonti NASA", "limits": "Limiti"},
        "tail": "(Dati NASA: GPM, SMAP, MODIS, POWER. Stima con limiti — verifica con la cooperativa.)",
        "limit": "Risposta dimostrativa. Il vero copilota (Claude API) sarà collegato dal Flux 2.",
    },
}


def _topic(q: str) -> str:
    q = (q or "").lower()
    for topic, kws in INTENT_KW.items():
        if any(k in q for k in kws):
            return topic
    return "generic"


def copilot_answer(question: str, context: dict[str, Any] | None, lang: str = "fr") -> dict[str, Any]:
    lang = _L(lang)
    C = COPILOT[lang]
    ctx = context or {}
    wb = ctx.get("water_budget") or {}
    pt = ctx.get("planting_timeline") or {}
    rots = ctx.get("rotations") or []
    risk = ctx.get("risk_level", "moderate")
    status = wb.get("status", "risky")
    avail, need, deficit = wb.get("available_water_mm", "?"), wb.get("crop_water_need_mm", "?"), wb.get("deficit_mm", "?")

    wline = (C["w_enough"] if status == "enough_water"
             else C["w_risky"] if status == "risky"
             else C["w_not"].format(deficit=deficit))

    topic = _topic(question)
    parts = [C["ack"]]
    if topic == "water":
        parts += [C["water_head"].format(avail=avail, need=need, crop=C["the_crop"]), wline]
    elif topic == "timing":
        parts.append(C["timing"].get(pt.get("recommendation", "wait"), C["timing"]["wait"]))
        if pt.get("best_window"):
            parts.append(C["timing_window"].format(window=pt["best_window"]))
    elif topic == "rotation":
        parts.append(C["rotation"].format(rot0=rots[0]["name"] if rots else "—"))
    elif topic == "irrigation":
        parts.append(C["irrigation"].format(wline=wline))
    elif topic == "soil":
        parts.append(C["soil"])
    else:
        parts += [C["risk"].get(risk, C["risk"]["moderate"]), wline]
    parts.append(C["tail"])

    # Réponse structurée : recommandation, eau, alternatives, actions (+ sources et limites).
    reco_line = C["timing"].get(pt.get("recommendation", "wait"), C["timing"]["wait"])
    if pt.get("best_window"):
        reco_line += " " + C["timing_window"].format(window=pt["best_window"])
    main_text = " ".join(parts[1:-1])
    if topic != "timing":
        main_text = (main_text + " " + reco_line).strip()
    sections = [
        {"key": "reco", "title": C["h"]["reco"], "text": main_text},
        {"key": "water", "title": C["h"]["water"], "text": C["water_head"].format(avail=avail, need=need, crop=C["the_crop"]) + " " + wline},
        {"key": "alt", "title": C["h"]["alt"], "text": C["alternatives"]},
        {"key": "actions", "title": C["h"]["actions"], "items": C["actions"]},
    ]
    return {
        "answer": " ".join(parts),
        "sections": sections,
        "sources": ["GPM IMERG", "SMAP", "MODIS/VIIRS", "NASA POWER"],
        "sources_title": C["h"]["sources"],
        "limitations": C["limit"],
        "limitations_title": C["h"]["limits"],
        "_mock": True,
    }


# --- Backtesting (mock) : « l'outil aurait-il prévenu ? » ------------------
BT_SEASONS = [("2015–2016", "El Niño"), ("2018–2019", "—"), ("2019–2020", "—"), ("2023–2024", "El Niño")]
BT_TXT = {
    "es": {
        "alert": {"low": "Sin alerta", "moderate": "Alerta moderada", "high": "Alerta de sequía"},
        "warned": "Avisó antes de la ventana de siembra",
        "missed": "Condiciones normales",
        "summary": "Field Shift habría avisado en {n} de {m} temporadas secas antes de la ventana de siembra.",
        "action": {"low": "Sembrar con normalidad", "moderate": "Esperar la lluvia y sembrar frijol", "high": "Cambiar a sorgo o frijol y cubrir el suelo"},
    },
    "fr": {
        "alert": {"low": "Pas d'alerte", "moderate": "Alerte modérée", "high": "Alerte sécheresse"},
        "warned": "Prévenu avant la fenêtre de semis",
        "missed": "Conditions normales",
        "summary": "Field Shift aurait prévenu lors de {n} saisons sèches sur {m} avant la fenêtre de semis.",
        "action": {"low": "Semer normalement", "moderate": "Attendre la pluie et semer du haricot", "high": "Passer au sorgho ou au haricot et couvrir le sol"},
    },
    "en": {
        "alert": {"low": "No alert", "moderate": "Moderate alert", "high": "Drought alert"},
        "warned": "Warned before the planting window",
        "missed": "Normal conditions",
        "summary": "Field Shift would have warned in {n} of {m} dry seasons before the planting window.",
        "action": {"low": "Plant as usual", "moderate": "Wait for rain and sow beans", "high": "Switch to sorghum or beans and cover the soil"},
    },
    "it": {
        "alert": {"low": "Nessun allarme", "moderate": "Allarme moderato", "high": "Allarme siccità"},
        "warned": "Avvisato prima della finestra di semina",
        "missed": "Condizioni normali",
        "summary": "Field Shift avrebbe avvisato in {n} stagioni secche su {m} prima della finestra di semina.",
        "action": {"low": "Seminare normalmente", "moderate": "Aspettare la pioggia e seminare fagioli", "high": "Passare a sorgo o fagioli e coprire il suolo"},
    },
}


def backtesting(payload: dict[str, Any]) -> dict[str, Any]:
    lang = _L(str(payload.get("lang", "fr")))
    T = BT_TXT[lang]
    lat = float(payload.get("latitude", 14.8))
    lon = float(payload.get("longitude", -90.5))
    base = _seed(lat, lon)

    seasons, warned = [], 0
    for i, (name, tag) in enumerate(BT_SEASONS):
        s = (base + i * 0.17) % 1.0
        el_nino = tag == "El Niño"
        rainfall_pct = round((45 if el_nino else 70) + s * 25)       # % du normal
        risk_score = int(max(5, min(98, (80 if el_nino else 45) + (0.7 - rainfall_pct / 100) * 60 - s * 15)))
        level = _risk_level(risk_score)
        did_warn = risk_score >= 50
        if did_warn:
            warned += 1
        seasons.append({
            "season": name, "tag": tag, "rainfall_pct": rainfall_pct,
            "risk_score": risk_score, "risk_level": level,
            "alert": T["alert"][level],
            "outcome": T["warned"] if did_warn else T["missed"],
            "warned": did_warn,
            "rainfall_anomaly_pct": rainfall_pct - 100,
            "soil_moisture": round(0.06 + (rainfall_pct / 100) * 0.2, 2),
            "ndvi_trend": round((rainfall_pct - 85) / 250, 2),
            "action": T["action"][level],
        })

    dry_total = sum(1 for x in seasons if x["risk_score"] >= 50 or x["tag"] == "El Niño")
    return {
        "seasons": seasons,
        "warned_count": warned,
        "total": len(seasons),
        "summary": T["summary"].format(n=warned, m=max(1, dry_total)),
        "_mock": True,
    }
