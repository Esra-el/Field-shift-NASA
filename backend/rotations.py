"""Field Shift — rotations calculées pour LE lieu et LA culture de l'agriculteur.

Au lieu de trois rotations fixes, on note chaque culture d'un petit catalogue
agronomique avec les données réelles du point :
  * température normale mois par mois (NASA POWER 1981-2020) sur SON cycle,
    risque de gel compris ;
  * pluie attendue sur son cycle (prévision Open-Meteo 16 j, puis normale
    ERA5/NASA POWER) + réserve du sol + irrigation, contre son besoin en eau ;
  * sa tolérance à la sécheresse ;
  * la pente de la parcelle (NASA SRTM) pour le risque d'érosion.
Chaque culture reçoit sa meilleure date de semis dans les mois qui viennent, puis
on assemble trois rotations (la plus sûre, équilibrée, meilleure récolte) et on
évalue la rotation actuelle de l'agriculteur avec les mêmes calculs.

Les valeurs agronomiques sont des ordres de grandeur (FAO, fiches culture) :
elles servent à comparer, pas à prédire un rendement. Le texte le dit.
"""
from __future__ import annotations

import unicodedata
from datetime import date, timedelta
from typing import Any

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

# need = besoin en eau sur le cycle (mm) ; days = durée semis -> récolte ;
# tmin = température moyenne minimale pour pousser ; lo/hi = plage idéale ; tmax = limite chaleur ;
# frost = supporte le gel (culture d'hiver) ; drought = tolérance à la sécheresse (0-1) ;
# yld = potentiel de récolte relatif (0-2) ; kind = cereal | legume | root | oil | cover.
CROPS: dict[str, dict[str, Any]] = {
    "maize":      dict(kind="cereal", need=520, days=120, tmin=12, lo=18, hi=30, tmax=36, frost=False, drought=0.3, yld=2.0),
    "sorghum":    dict(kind="cereal", need=420, days=110, tmin=15, lo=22, hi=33, tmax=40, frost=False, drought=0.85, yld=1.4),
    "millet":     dict(kind="cereal", need=360, days=95,  tmin=16, lo=24, hi=34, tmax=42, frost=False, drought=0.95, yld=1.0),
    "wheat":      dict(kind="cereal", need=450, days=170, tmin=3,  lo=10, hi=22, tmax=30, frost=True,  drought=0.5, yld=1.8),
    "barley":     dict(kind="cereal", need=380, days=150, tmin=2,  lo=8,  hi=20, tmax=30, frost=True,  drought=0.65, yld=1.4),
    "beans":      dict(kind="legume", need=350, days=85,  tmin=12, lo=16, hi=26, tmax=31, frost=False, drought=0.3, yld=1.1),
    "cowpea":     dict(kind="legume", need=300, days=80,  tmin=16, lo=22, hi=33, tmax=38, frost=False, drought=0.85, yld=1.0),
    "groundnut":  dict(kind="legume", need=450, days=120, tmin=16, lo=22, hi=30, tmax=36, frost=False, drought=0.6, yld=1.2),
    "soybean":    dict(kind="legume", need=450, days=110, tmin=14, lo=20, hi=30, tmax=35, frost=False, drought=0.4, yld=1.5),
    "chickpea":   dict(kind="legume", need=300, days=130, tmin=5,  lo=12, hi=25, tmax=32, frost=True,  drought=0.85, yld=1.0),
    "faba":       dict(kind="legume", need=380, days=150, tmin=3,  lo=8,  hi=20, tmax=28, frost=True,  drought=0.4, yld=1.1),
    "lentil":     dict(kind="legume", need=280, days=120, tmin=4,  lo=10, hi=22, tmax=30, frost=True,  drought=0.75, yld=0.9),
    "sweetpotato": dict(kind="root",  need=450, days=120, tmin=15, lo=20, hi=30, tmax=35, frost=False, drought=0.6, yld=1.4),
    "sunflower":  dict(kind="oil",    need=450, days=110, tmin=10, lo=18, hi=28, tmax=35, frost=False, drought=0.65, yld=1.2),
    "mucuna":     dict(kind="cover",  need=300, days=90,  tmin=16, lo=22, hi=32, tmax=38, frost=False, drought=0.7, yld=0.0),
    "vetch_oats": dict(kind="cover",  need=250, days=120, tmin=2,  lo=8,  hi=20, tmax=28, frost=True,  drought=0.5, yld=0.0),
}
LEGUMES = {k for k, c in CROPS.items() if c["kind"] == "legume"}
FOOD = {k for k, c in CROPS.items() if c["kind"] != "cover"}
NFIX = LEGUMES | {"mucuna", "vetch_oats"}

NAMES = {
    "fr": {"maize": "maïs", "sorghum": "sorgho", "millet": "mil", "wheat": "blé", "barley": "orge", "beans": "haricot",
           "cowpea": "niébé", "groundnut": "arachide", "soybean": "soja", "chickpea": "pois chiche", "faba": "fève",
           "lentil": "lentille", "sweetpotato": "patate douce", "sunflower": "tournesol",
           "mucuna": "couverture mucuna", "vetch_oats": "couverture vesce-avoine"},
    "en": {"maize": "maize", "sorghum": "sorghum", "millet": "millet", "wheat": "wheat", "barley": "barley", "beans": "beans",
           "cowpea": "cowpea", "groundnut": "groundnut", "soybean": "soybean", "chickpea": "chickpea", "faba": "faba bean",
           "lentil": "lentil", "sweetpotato": "sweet potato", "sunflower": "sunflower",
           "mucuna": "mucuna cover crop", "vetch_oats": "vetch-oat cover crop"},
    "it": {"maize": "mais", "sorghum": "sorgo", "millet": "miglio", "wheat": "frumento", "barley": "orzo", "beans": "fagioli",
           "cowpea": "fagiolo dall'occhio", "groundnut": "arachidi", "soybean": "soia", "chickpea": "cece", "faba": "fava",
           "lentil": "lenticchia", "sweetpotato": "patata dolce", "sunflower": "girasole",
           "mucuna": "copertura di mucuna", "vetch_oats": "copertura veccia-avena"},
}

# Mots-clés (FR/EN/IT/ES, sans accents) pour reconnaître une culture écrite librement.
ALIASES = {
    "maize": ["mais", "maize", "corn", "granoturco", "granturco", "maiz"],
    "sorghum": ["sorgho", "sorghum", "sorgo"],
    "millet": ["mil", "millet", "miglio", "mijo"],
    "wheat": ["ble", "wheat", "frumento", "grano", "trigo"],
    "barley": ["orge", "barley", "orzo", "cebada"],
    "beans": ["haricot", "bean", "fagiol", "frijol", "judia"],
    "cowpea": ["niebe", "cowpea", "dall'occhio", "caupi"],
    "groundnut": ["arachide", "groundnut", "peanut", "arachid", "cacahuete"],
    "soybean": ["soja", "soy", "soia"],
    "chickpea": ["pois chiche", "chickpea", "cece", "ceci", "garbanzo"],
    "faba": ["feve", "faba", "fava", "haba"],
    "lentil": ["lentille", "lentil", "lenticchi", "lenteja"],
    "sweetpotato": ["patate douce", "sweet potato", "patata dolce", "camote", "batata"],
    "sunflower": ["tournesol", "sunflower", "girasole", "girasol"],
    "mucuna": ["mucuna"],
    "vetch_oats": ["vesce", "vetch", "veccia", "couverture", "cover", "copertura", "jachere", "fallow", "maggese"],
}

TX = {
    "fr": {
        "fit": "{c} ({m1}–{m2}) : besoin d'environ {need} mm, environ {avail} mm attendus ; {t} °C en moyenne (idéal {lo}–{hi} °C).",
        "cold": "{c} : trop froid sur ce cycle ({t} °C, il lui faut au moins {tmin} °C).",
        "frost": "{c} : risque de gel sur ce cycle (mois le plus froid {t} °C) et cette culture ne le supporte pas.",
        "hot": "{c} : chaleur au-dessus de sa limite ({t} °C pour {tmax} °C max).",
        "legume": "{c} fixe l'azote de l'air : la culture suivante a besoin de moins d'engrais.",
        "cover": "{c} garde le sol couvert entre deux cultures : moins d'érosion et d'évaporation, plus de matière organique.",
        "mono": "La même culture chaque saison ne coupe pas le cycle des ravageurs et des maladies.",
        "slope": "Pente de la parcelle : {p} % (NASA SRTM) — risque d'érosion {lvl}.",
        "lvl": {"low": "faible", "moderate": "modéré", "high": "élevé"},
        "safest": "Les cultures les plus sûres ici avec l'eau et les températures attendues, puis une couverture pour protéger le sol.",
        "balanced": "Une légumineuse pour nourrir le sol, puis la céréale qui convient le mieux à votre saison.",
        "highest_yield": "La culture au meilleur potentiel de récolte ici, à suivre de près si l'eau manque.",
        "current": "Votre rotation actuelle, évaluée avec exactement les mêmes calculs pour pouvoir comparer.",
        "act_sow": "Semer {c} vers le {d}.",
        "act_then": "Puis {c} vers le {d}.",
        "act_res": "Laisser les résidus de {c} sur le sol après la récolte.",
        "act_contour": "Pente forte : semer en courbes de niveau et ne jamais laisser le sol nu.",
        "act_water": "L'eau risque de manquer pour {c} : semer moins dense ou prévoir un arrosage d'appoint.",
        "act_keep": "Si vous la gardez : couvrir le sol entre deux saisons et ajouter une légumineuse une saison sur deux.",
        "gap_values": "Les besoins en eau et températures des cultures sont des moyennes générales, pas vos variétés.",
        "gap_slope": "La pente de votre parcelle n'a pas pu être lue (NASA SRTM indisponible ici).",
    },
    "en": {
        "fit": "{c} ({m1}–{m2}): needs about {need} mm, about {avail} mm expected; {t} °C on average (ideal {lo}–{hi} °C).",
        "cold": "{c}: too cold over this cycle ({t} °C, it needs at least {tmin} °C).",
        "frost": "{c}: frost risk over this cycle (coldest month {t} °C) and this crop cannot take it.",
        "hot": "{c}: heat above its limit ({t} °C vs {tmax} °C max).",
        "legume": "{c} fixes nitrogen from the air: the next crop needs less fertiliser.",
        "cover": "{c} keeps the soil covered between crops: less erosion and evaporation, more organic matter.",
        "mono": "Growing the same crop every season does not break pest and disease cycles.",
        "slope": "Field slope: {p}% (NASA SRTM) — {lvl} erosion risk.",
        "lvl": {"low": "low", "moderate": "moderate", "high": "high"},
        "safest": "The safest crops here for the expected water and temperatures, then a cover crop to protect the soil.",
        "balanced": "A legume to feed the soil, then the cereal that best suits your season.",
        "highest_yield": "The crop with the best harvest potential here, to watch closely if water runs short.",
        "current": "Your current rotation, assessed with exactly the same calculations so you can compare.",
        "act_sow": "Sow {c} around {d}.",
        "act_then": "Then {c} around {d}.",
        "act_res": "Leave the {c} residue on the soil after harvest.",
        "act_contour": "Steep slope: sow along contour lines and never leave the soil bare.",
        "act_water": "Water may run short for {c}: sow less densely or plan some extra watering.",
        "act_keep": "If you keep it: cover the soil between seasons and add a legume every other season.",
        "gap_values": "Crop water needs and temperatures are general averages, not your varieties.",
        "gap_slope": "Your field's slope could not be read (NASA SRTM not available here).",
    },
    "it": {
        "fit": "{c} ({m1}–{m2}): servono circa {need} mm, ne sono attesi circa {avail} mm; {t} °C in media (ideale {lo}–{hi} °C).",
        "cold": "{c}: troppo freddo in questo ciclo ({t} °C, ne servono almeno {tmin} °C).",
        "frost": "{c}: rischio gelo in questo ciclo (mese più freddo {t} °C) e questa coltura non lo sopporta.",
        "hot": "{c}: caldo oltre il suo limite ({t} °C contro {tmax} °C max).",
        "legume": "{c} fissa l'azoto dell'aria: la coltura successiva ha bisogno di meno concime.",
        "cover": "{c} tiene il suolo coperto tra due colture: meno erosione ed evaporazione, più sostanza organica.",
        "mono": "La stessa coltura ogni stagione non interrompe il ciclo di parassiti e malattie.",
        "slope": "Pendenza del campo: {p}% (NASA SRTM) — rischio di erosione {lvl}.",
        "lvl": {"low": "basso", "moderate": "moderato", "high": "alto"},
        "safest": "Le colture più sicure qui con l'acqua e le temperature attese, poi una copertura per proteggere il suolo.",
        "balanced": "Un legume per nutrire il suolo, poi il cereale più adatto alla tua stagione.",
        "highest_yield": "La coltura con il miglior potenziale di raccolto qui, da seguire da vicino se manca l'acqua.",
        "current": "La tua rotazione attuale, valutata con esattamente gli stessi calcoli per poterle confrontare.",
        "act_sow": "Seminare {c} verso il {d}.",
        "act_then": "Poi {c} verso il {d}.",
        "act_res": "Lasciare i residui di {c} sul suolo dopo il raccolto.",
        "act_contour": "Pendenza forte: seminare seguendo le curve di livello e non lasciare mai il suolo nudo.",
        "act_water": "L'acqua può mancare per {c}: seminare meno fitto o prevedere un'irrigazione di soccorso.",
        "act_keep": "Se la tieni: coprire il suolo tra due stagioni e aggiungere un legume una stagione su due.",
        "gap_values": "Fabbisogni d'acqua e temperature delle colture sono medie generali, non le tue varietà.",
        "gap_slope": "Non è stato possibile leggere la pendenza del campo (NASA SRTM non disponibile qui).",
    },
}
MONTH_ABBR = {
    "fr": ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."],
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "it": ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"],
}


def _norm(s: str) -> str:
    return unicodedata.normalize("NFD", str(s).lower()).encode("ascii", "ignore").decode()


def crop_key(text: str) -> str | None:
    """Clé du catalogue pour un nom de culture libre (« Maïs », « fagioli »…), sinon None."""
    s = _norm(text).strip()
    if s in CROPS:
        return s
    for k in ["sweetpotato", "chickpea", "cowpea", "faba"] + list(ALIASES):  # les noms composés d'abord
        for a in ALIASES[k]:
            if a in s:
                return k
    return None


def parse_rotation(text: str) -> list[str]:
    # Séparateurs AVANT de normaliser : la normalisation ASCII supprime la flèche « → ».
    raw = str(text)
    for sep in ("->", "→", ",", "/", ";", "+"):
        raw = raw.replace(sep, "|")
    parts = [p for p in raw.split("|") if p.strip()]
    keys = [crop_key(p) for p in parts]
    return [k for k in keys if k]


def erosion_level(slope_pct: float | None) -> str | None:
    if slope_pct is None:
        return None
    return "high" if slope_pct >= 8 else "moderate" if slope_pct >= 3 else "low"


class Site:
    """Conditions du lieu, lues une fois : normales mensuelles, prévision, sol, irrigation."""

    def __init__(self, live: dict[str, Any], today: date, soil_moisture: float, retention: float, irrigation_mm: float):
        self.today = today
        self.t_month = live.get("temp_normal_monthly") or {}
        self.rain_month = live.get("clim_mm_day") or {}
        self.fc = {x["date"]: x.get("rain_mm") or 0.0 for x in live.get("forecast") or []}
        self.soil_mm = soil_moisture * 600 * retention * 0.5
        self.irrigation_mm = irrigation_mm
        self.recent_t = live.get("temperature_7d_c")

    def rain(self, start: date, days: int) -> float:
        tot = 0.0
        for i in range(days):
            d = start + timedelta(days=i)
            v = self.fc.get(d.isoformat())
            tot += v if v is not None else self.rain_month.get(MONTHS[d.month - 1], 0.0)
        return tot

    def temps(self, start: date, days: int) -> tuple[float | None, float | None]:
        if not self.t_month:
            return self.recent_t, self.recent_t
        vals = [self.t_month[MONTHS[(start + timedelta(days=i)).month - 1]] for i in range(0, days, 5)]
        return sum(vals) / len(vals), min(vals)


def assess(site: Site, key: str, start: date, first: bool) -> dict[str, Any]:
    """Note une culture semée à `start` : eau, température, gel. Score 0-1."""
    c = CROPS[key]
    t_mean, t_min = site.temps(start, c["days"])
    avail = site.rain(start, c["days"]) * 0.75 + site.irrigation_mm + (site.soil_mm if first else site.soil_mm * 0.4)
    cov = min(1.0, avail / c["need"])
    cov_eff = cov + c["drought"] * 0.25 * (1 - cov)  # une culture rustique supporte un peu mieux le manque d'eau
    issue = None
    if t_mean is None:
        t_score = 0.7
    elif t_mean < c["tmin"]:
        t_score, issue = 0.0, "cold"
    elif t_mean > c["tmax"]:
        t_score, issue = 0.0, "hot"
    elif t_mean < c["lo"]:
        t_score = 0.35 + 0.65 * (t_mean - c["tmin"]) / max(1, c["lo"] - c["tmin"])
    elif t_mean > c["hi"]:
        t_score = 0.35 + 0.65 * (c["tmax"] - t_mean) / max(1, c["tmax"] - c["hi"])
    else:
        t_score = 1.0
    if t_min is not None and t_min < 4 and not c["frost"] and issue is None:
        t_score, issue = t_score * 0.25, "frost"
    score = t_score * (0.15 + 0.85 * cov_eff)
    return dict(key=key, start=start, end=start + timedelta(days=c["days"]), t_mean=t_mean, t_min=t_min,
                avail=round(avail), need=c["need"], cov=cov, score=round(score, 3), issue=issue)


def best_start(site: Site, key: str, earliest: date, first: bool, horizon_days: int = 210) -> dict[str, Any]:
    """Meilleure date de semis entre `earliest` et ~7 mois plus tard (pas de 15 jours)."""
    cands = [assess(site, key, earliest + timedelta(days=k), first and k < 30) for k in range(0, horizon_days, 15)]
    top = max(c["score"] for c in cands)
    # La date la plus PROCHE qui est presque aussi bonne que la meilleure : on ne fait pas
    # attendre six mois l'agriculteur pour gagner quelques points.
    return next(c for c in cands if c["score"] >= top - 0.08)


def build(live: dict[str, Any], today: date, sow: date, farmer_crop: str, current_txt: str, soil_moisture: float,
          retention: float, irrigation_mm: float, lang: str, risk_level: str) -> list[dict[str, Any]] | None:
    """Trois rotations calculées pour le lieu + la rotation actuelle. None si les normales manquent."""
    if not live.get("clim_mm_day"):
        return None
    lang = lang if lang in TX else "fr"
    X, N, MA = TX[lang], NAMES[lang], MONTH_ABBR[lang]
    site = Site(live, today, soil_moisture, retention, irrigation_mm)
    slope = live.get("slope_pct")
    ero = erosion_level(slope)
    fkey = crop_key(farmer_crop) or "maize"

    # Chaque culture a sa propre saison (une culture d'hiver peut se semer maintenant même
    # si le maïs doit attendre le printemps) : on part de la semaine prochaine, pas de la
    # fenêtre de semis de la culture de l'agriculteur.
    sow = today + timedelta(days=7)
    first = {k: best_start(site, k, sow, True) for k in CROPS}

    def pick(keys, weight=lambda a: a["score"]):
        return max(keys, key=lambda k: weight(first[k]))

    def chain(keys: list[str], keep_order: bool = False) -> list[dict[str, Any]]:
        # Les cultures suivent l'ordre de LEUR meilleure saison (ex. la saison des pluies
        # pour le mil), sinon une culture semée hors saison bloquerait la bonne fenêtre.
        if not keep_order:
            keys = sorted(keys, key=lambda k: first[k]["start"])
        out, at = [], sow
        for i, k in enumerate(keys):
            a = best_start(site, k, at, i == 0, horizon_days=365 if i else 210)
            out.append(a)
            at = a["end"] + timedelta(days=10)
        return out

    def cover_after(prev_end: date) -> str:
        return max(("mucuna", "vetch_oats"), key=lambda k: best_start(site, k, prev_end + timedelta(days=10), False)["score"])

    cereals = [k for k in CROPS if CROPS[k]["kind"] == "cereal"]
    food_dry = [k for k in FOOD]
    # 1) La plus sûre : la culture qui tient le mieux l'eau attendue (rustique), une légumineuse rustique, une couverture.
    s1 = pick(food_dry, lambda a: a["score"] * (0.6 + 0.4 * CROPS[a["key"]]["drought"]) * (0.7 + 0.3 * a["cov"]))
    s2 = pick([k for k in LEGUMES if k != s1], lambda a: a["score"] * (0.6 + 0.4 * CROPS[a["key"]]["drought"]))
    safest = [s2, s1] if CROPS[s1]["kind"] != "legume" else [s1, pick([k for k in cereals], lambda a: a["score"] * (0.6 + 0.4 * CROPS[a["key"]]["drought"]))]
    # 2) Équilibrée : la meilleure légumineuse, puis la céréale de l'agriculteur si elle convient, sinon la meilleure.
    b1 = pick(list(LEGUMES))
    fa = first[fkey]
    b2 = fkey if fkey in FOOD and fkey != b1 and fa["score"] >= 0.5 else pick(cereals)
    balanced = [b1, b2]
    # 3) Meilleure récolte : la culture de l'agriculteur si elle convient, sinon le meilleur potentiel ; puis une légumineuse.
    y1 = fkey if fkey in FOOD and fa["score"] >= 0.55 else pick(list(FOOD), lambda a: a["score"] * (0.4 + 0.6 * CROPS[a["key"]]["yld"] / 2))
    leg_alt = [k for k in LEGUMES if k not in (y1, b1)]
    y2 = pick(leg_alt) if leg_alt and first[pick(leg_alt)]["score"] >= first[b1]["score"] - 0.15 else pick([k for k in LEGUMES if k != y1])
    highest = [y1, y2]

    plans = []
    for typ, keys in (("safest", safest), ("balanced", balanced), ("highest_yield", highest)):
        steps = chain(keys)
        cov_k = cover_after(steps[-1]["end"])
        steps.append(best_start(site, cov_k, steps[-1]["end"] + timedelta(days=10), False))
        plans.append((typ, steps))

    cur_keys = parse_rotation(current_txt) or [fkey, fkey]
    if len(cur_keys) == 1:
        cur_keys = cur_keys * 2
    plans.append(("current", chain(cur_keys[:3], keep_order=True)))

    f_need = CROPS[fkey]["need"]
    out = []
    for typ, steps in plans:
        food = [s for s in steps if CROPS[s["key"]]["kind"] != "cover"]
        mean_need = sum(s["need"] for s in food) / max(1, len(food))
        saving = max(0, round(100 * (1 - mean_need / f_need))) if typ != "current" else 0
        mean_score = sum(s["score"] for s in food) / max(1, len(food))
        mean_cov = sum(s["cov"] for s in food) / max(1, len(food))
        has_leg = any(s["key"] in NFIX for s in steps)
        has_cover = any(CROPS[s["key"]]["kind"] == "cover" for s in steps)
        mono = len({s["key"] for s in steps}) == 1
        soil = "high" if has_leg and has_cover else "medium" if has_leg or has_cover else "low"
        if mono:
            soil = "low"
        if ero == "high" and not has_cover:
            soil = "low"
        yld = sum(CROPS[s["key"]]["yld"] * s["score"] for s in food) / max(1, len(food))
        yield_lvl = "high" if yld >= 1.1 else "medium" if yld >= 0.55 else "low"
        if typ == "current":
            risk = risk_level
        else:
            risk = "low" if mean_score >= 0.7 and mean_cov >= 0.8 else "high" if mean_score < 0.4 or mean_cov < 0.5 else "moderate"

        def mon(d: date) -> str:
            return MA[d.month - 1]

        evidence = []
        for s in steps:
            c = CROPS[s["key"]]
            nm = N[s["key"]].capitalize()
            t = round(s["t_mean"]) if s["t_mean"] is not None else "—"
            if s["issue"] == "cold":
                evidence.append(X["cold"].format(c=nm, t=t, tmin=c["tmin"]))
            elif s["issue"] == "hot":
                evidence.append(X["hot"].format(c=nm, t=t, tmax=c["tmax"]))
            elif s["issue"] == "frost":
                evidence.append(X["frost"].format(c=nm, t=round(s["t_min"])))
            else:
                evidence.append(X["fit"].format(c=nm, m1=mon(s["start"]), m2=mon(s["end"]), need=s["need"],
                                                avail=s["avail"], t=t, lo=c["lo"], hi=c["hi"]))
        legs = [s["key"] for s in steps if s["key"] in LEGUMES]
        if legs:
            evidence.append(X["legume"].format(c=N[legs[0]].capitalize()))
        covers = [s["key"] for s in steps if CROPS[s["key"]]["kind"] == "cover"]
        if covers:
            evidence.append(X["cover"].format(c=N[covers[0]].capitalize()))
        if mono:
            evidence.append(X["mono"])
        if ero:
            evidence.append(X["slope"].format(p=slope, lvl=X["lvl"][ero]))

        actions = [X["act_sow"].format(c=N[steps[0]["key"]], d=steps[0]["start"].strftime("%d/%m/%Y"))]
        for s in steps[1:]:
            actions.append(X["act_then"].format(c=N[s["key"]], d=s["start"].strftime("%d/%m/%Y")))
        dry = [s for s in food if s["cov"] < 0.75]
        if dry:
            actions.append(X["act_water"].format(c=N[dry[0]["key"]]))
        if ero in ("moderate", "high"):
            actions.append(X["act_contour"])
        if typ == "current":
            actions.append(X["act_keep"])
        elif food:
            actions.append(X["act_res"].format(c=N[food[-1]["key"]]))

        name = " → ".join(N[s["key"]].capitalize() for s in steps)
        out.append({
            "type": typ, "name": name, "crops": [s["key"] for s in steps],
            "schedule": [{"crop": s["key"], "start": s["start"].isoformat(), "end": s["end"].isoformat(),
                          "score": s["score"], "water_need_mm": s["need"], "water_expected_mm": s["avail"]} for s in steps],
            "water_saving": "high" if saving >= 25 else "medium" if saving >= 10 else "low", "water_saving_pct": saving,
            "soil_benefit": soil, "yield_potential": yield_lvl, "risk": risk,
            "fit_score": round(mean_score * 100),
            "reason": X[typ], "actions": actions[:5], "evidence": evidence[:6],
            "is_current": typ == "current",
        })
    return out
