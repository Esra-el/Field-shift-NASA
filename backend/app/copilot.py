"""Explainable AI copilot — OWNED BY THE `ai` AGENT.

Provider: Google Gemini (free tier) via the `google-genai` SDK. Chosen so the
NASA Space Apps demo costs nothing — a free AI Studio key powers it, and with no
key it still works via the deterministic fallback below.

Interface (keep these signatures; the pipeline + API depend on them):

    explain(recommendation: dict, field: dict, lang: str = "es") -> str
    answer(question: str, recommendation: dict, field: dict, lang: str = "es") -> str

Rules the `ai` agent must honor:
  * EXPLAIN the recommendation; never invent numbers or agronomic facts.
  * Cite the NASA sources behind the numbers.
  * Simple, farmer-friendly language.
  * MUST keep a deterministic fallback when no API key is set or the API errors —
    the live demo can never hard-fail on this call.

REPLY LANGUAGE
  * explain()  — has no question, so it replies in the language the user SELECTED
    in the app (the `lang` toggle): FR / EN / IT, or ES for the pilot region.
  * answer()   — replies in the language the farmer TYPED the question in (the
    input drives the output). A French question gets a French answer, an English
    question an English answer, even if the app toggle is set to something else.
    The live model mirrors the question's language itself; the no-AI fallback
    uses a small language detector. Either way the reply is ONE language, never
    a French/English mix.

HOW IT WORKS
  One Gemini call (a fast, free-tier Flash model) turns the structured
  Recommendation into a short, farmer-friendly explanation. The model gets TWO
  guardrails:
    1. SYSTEM PROMPT (`config.system_instruction`) — locks it to EXPLAIN-ONLY:
       never invent a number, cite the NASA source behind each one, stay simple,
       end with a next action, reply in ONE language, and (for answers) refuse
       anything the data lacks.
    2. GROUNDING — the recommendation + field dicts are serialized into the
       request `contents` as the ONLY facts the model may use. No tools, no
       outside knowledge.
  Every failure mode — no API key, network/timeout error, a blocked/empty
  response — degrades to the deterministic template, so the demo never breaks and
  these functions never raise.
"""
from __future__ import annotations

import json
import logging
import os
import re

_log = logging.getLogger("copilot")
# Last copilot failure reason (NEVER the API key) — surfaced in logs and on
# /health so a silent fallback in production is diagnosable. None after success.
_LAST_ERROR = None

# Free-tier Gemini model. gemini-3.1-flash-lite is fast (~3s) and reliable for
# this simple rewording task; the heavier gemini-3.8/3.6-flash were overloaded
# (503/504) when tested on 2026-11-14, and gemini-2.5-flash is deprecated.
# flash-lite is purpose-built for high-volume, low-latency tasks. Override via
# env GEMINI_MODEL if you want a different one.
_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")
_MAX_TOKENS = 500          # short output -> low latency
_TIMEOUT_MS = 10_000       # per-attempt; API minimum is 10s (8s is rejected 400)
_NASA_SOURCES = (
    "NASA POWER (weather, solar radiation, evapotranspiration), "
    "GPM IMERG (rainfall), SMAP (soil moisture), MODIS/VIIRS (NDVI vegetation)"
)
_LANGS = ("en", "es", "fr", "it")


# --------------------------------------------------------------------------- #
# Language detection for the no-AI fallback (the live model detects it itself)
# --------------------------------------------------------------------------- #
# Distinctive, high-frequency markers per language. ES/FR/IT share Latin roots,
# so we lean on words that are unique to one language ("aide"=FR, "ayuda"=ES,
# "aiuto"=IT, "help"=EN; "besoin"/"necesito"/"bisogno"/"need") plus accented
# characters. A weak/ambiguous signal keeps the app's selected language.
_LANG_MARKERS = {
    "en": {"the", "what", "when", "how", "should", "need", "help", "water", "drought",
           "plant", "my", "soil", "rain", "why", "can", "do", "is", "and", "for", "hello"},
    "es": {"el", "la", "los", "que", "cómo", "cuándo", "por", "para", "qué", "agua",
           "sequía", "sembrar", "debo", "necesito", "ayuda", "cultivo", "lluvia",
           "suelo", "mi", "está", "hola", "cuánta", "cualquier", "cosa", "hacer",
           "ahora", "puedo"},
    "fr": {"le", "la", "les", "que", "comment", "quand", "pour", "quoi", "dois",
           "besoin", "aide", "eau", "sécheresse", "semer", "sol", "pluie", "est",
           "quelle", "mon", "bonjour", "je", "faire"},
    "it": {"il", "la", "che", "come", "quando", "per", "cosa", "devo", "bisogno",
           "aiuto", "acqua", "siccità", "seminare", "suolo", "pioggia", "quale",
           "mio", "ciao", "ho", "fare"},
}
_LANG_CHARS = {"es": "ñ¿¡", "fr": "çàâêëîïôûœ", "it": "àèéìòù"}


def _detect_lang(text: str, default: str = "es") -> str:
    """Best-effort guess of the language `text` is written in (one of _LANGS).

    Returns `default` when the text is too short or the signal is ambiguous, so
    a one-word "ok?" never flips the language away from what the user chose.
    """
    default = default if default in _LANGS else "es"
    t = (text or "").lower()
    if len(t.strip()) < 2:
        return default
    tokens = set(re.findall(r"[a-zà-ÿñ]+", t))
    scores = {lg: len(tokens & words) for lg, words in _LANG_MARKERS.items()}
    for lg, chars in _LANG_CHARS.items():
        if any(c in t for c in chars):
            scores[lg] += 2
    best = max(scores, key=scores.get)
    ranked = sorted(scores.values(), reverse=True)
    # No real signal, or a tie for first place -> trust the app's chosen language.
    if scores[best] == 0 or (len(ranked) > 1 and ranked[0] == ranked[1]):
        return default
    return best


# --------------------------------------------------------------------------- #
# Deterministic fallback (no API) — the live-demo safety net.
# Built ENTIRELY from structured fields + per-language word tables, so the output
# is always one clean language (the engine's localized prose is NOT spliced in,
# which is what used to produce French/English mixes).
# --------------------------------------------------------------------------- #
_RISK_WORD = {
    "en": {"low": "low", "moderate": "moderate", "high": "high"},
    "es": {"low": "bajo", "moderate": "moderado", "high": "alto"},
    "fr": {"low": "faible", "moderate": "modéré", "high": "élevé"},
    "it": {"low": "basso", "moderate": "moderato", "high": "alto"},
}
_ACTION_WORD = {
    "en": {"plant_now": "plant now", "switch_crop": "switch to a hardier crop",
           "wait": "wait before planting"},
    "es": {"plant_now": "sembrar ahora", "switch_crop": "cambiar a un cultivo más resistente",
           "wait": "esperar antes de sembrar"},
    "fr": {"plant_now": "semer maintenant", "switch_crop": "passer à une culture plus résistante",
           "wait": "attendre avant de semer"},
    "it": {"plant_now": "seminare ora", "switch_crop": "passare a una coltura più resistente",
           "wait": "attendere prima di seminare"},
}
_WATER_OK = {
    "en": "There is enough water for now.",
    "es": "Hay suficiente agua por ahora.",
    "fr": "Il y a assez d'eau pour l'instant.",
    "it": "C'è abbastanza acqua per ora.",
}
_WATER_SHORT = {
    "en": "Water is short by about {d} mm.",
    "es": "Falta agua, unos {d} mm.",
    "fr": "Il manque de l'eau, environ {d} mm.",
    "it": "Manca acqua, circa {d} mm.",
}
_WATER_SHORT_NONUM = {
    "en": "There is not enough water right now.",
    "es": "No hay suficiente agua ahora mismo.",
    "fr": "Il n'y a pas assez d'eau en ce moment.",
    "it": "Non c'è abbastanza acqua in questo momento.",
}
# {rl}=risk word, {rs}=risk score, {water}=water sentence, {ac}=action phrase.
_FALLBACK_TEMPLATES = {
    "en": "Drought risk is {rl} ({rs}/100). {water} Recommendation: {ac}. "
          "(Data: NASA POWER, GPM IMERG, SMAP, MODIS NDVI.)",
    "es": "El riesgo de sequía es {rl} ({rs}/100). {water} Recomendación: {ac}. "
          "(Datos: NASA POWER, GPM IMERG, SMAP, MODIS NDVI.)",
    "fr": "Le risque de sécheresse est {rl} ({rs}/100). {water} Recommandation : {ac}. "
          "(Données : NASA POWER, GPM IMERG, SMAP, MODIS NDVI.)",
    "it": "Il rischio di siccità è {rl} ({rs}/100). {water} Raccomandazione: {ac}. "
          "(Dati: NASA POWER, GPM IMERG, SMAP, MODIS NDVI.)",
}
# Short opener for a Q&A fallback, so it reads as a reply, not a bare summary.
_ANSWER_OPENER = {
    "en": "Here is what the data shows. ",
    "es": "Esto es lo que muestran los datos. ",
    "fr": "Voici ce que montrent les données. ",
    "it": "Ecco cosa mostrano i dati. ",
}
# Developer hint appended ONLY when no key is configured at all. When a key IS
# set but the call fails, we show the clean rule-based answer with no developer
# noise — telling a user to "configure GEMINI_API_KEY" they already set is wrong
# and confusing; the real reason is logged instead (see _call_model).
_NO_KEY_HINT = {
    "en": " [Set GEMINI_API_KEY for full AI answers.]",
    "es": " [Configure GEMINI_API_KEY para respuestas de IA completas.]",
    "fr": " [Configurez GEMINI_API_KEY pour des réponses IA complètes.]",
    "it": " [Imposta GEMINI_API_KEY per risposte IA complete.]",
}


def _loc(table: dict, lang: str) -> dict:
    return table.get(lang) or table["es"]


def _water_sentence(recommendation: dict, lang: str) -> str:
    wb = recommendation.get("water_budget", {}) or {}
    status = wb.get("status")
    if status == "enough_water":
        return _loc(_WATER_OK, lang)
    deficit = wb.get("deficit_mm")
    if isinstance(deficit, (int, float)) and deficit > 0:
        return _loc(_WATER_SHORT, lang).format(d=int(round(deficit)))
    return _loc(_WATER_SHORT_NONUM, lang)


def _fallback_summary(recommendation: dict, lang: str) -> str:
    rl_key = str(recommendation.get("risk_level", "")).lower()
    rl = _loc(_RISK_WORD, lang).get(rl_key, rl_key or "?")
    rs = recommendation.get("risk_score", "?")
    water = _water_sentence(recommendation, lang)
    pt = recommendation.get("planting_timeline", {}) or {}
    ac_key = str(pt.get("recommendation", "")).lower()
    ac = _loc(_ACTION_WORD, lang).get(ac_key, ac_key.replace("_", " ") or "?")
    return _loc(_FALLBACK_TEMPLATES, lang).format(rl=rl, rs=rs, water=water, ac=ac)


def _fallback_explain(recommendation: dict, field: dict, lang: str = "es") -> str:
    return _fallback_summary(recommendation, lang)


def _fallback_answer(question: str, recommendation: dict, field: dict, lang: str = "es") -> str:
    # The answer echoes the language the question was written in (input-driven).
    reply_lang = _detect_lang(question, default=lang)
    base = _loc(_ANSWER_OPENER, reply_lang) + _fallback_summary(recommendation, reply_lang)
    if _api_key():
        # Key present but the live call failed — give the clean answer, no noise.
        return base
    return base + _loc(_NO_KEY_HINT, reply_lang)


# --------------------------------------------------------------------------- #
# Prompt construction
# --------------------------------------------------------------------------- #
def _system_prompt(lang: str, mode: str) -> str:
    rules = (
        "You are Field Shift's copilot. You help a rain-fed farmer understand a "
        "drought-planning recommendation.\n"
        "RULES:\n"
        "- EXPLAIN ONLY. Use ONLY the numbers and facts in the DATA the user gives "
        "you. Never invent a number, a date, or an agronomic fact.\n"
        "- When you mention a measurement, name the NASA source behind it: "
        f"{_NASA_SOURCES}.\n"
        "- Use simple, warm, farmer-friendly words. No jargon.\n"
        "- Be short and concrete, and finish with one clear next action.\n"
    )
    if mode == "answer":
        # Input-driven: the reply language follows the farmer's question, not the
        # app toggle. The model detects and mirrors it.
        rules += (
            "- LANGUAGE: write your ENTIRE reply in the SAME language as the "
            "farmer's question below. If the question is in English, answer in "
            "English; in French, answer in French; in Spanish, Spanish; in "
            "Italian, Italian. Do NOT mix languages, and do not use any other "
            "language even if the DATA is written in a different one.\n"
            "- Answer using ONLY that DATA. If the question asks for something the "
            "DATA does not have that information, say so plainly and do not guess.\n"
        )
    else:
        reply_lang = {"en": "English", "es": "Spanish", "fr": "French", "it": "Italian"}.get(lang, "Spanish")
        rules += (
            f"- LANGUAGE: write your ENTIRE reply in {reply_lang}. Do NOT mix "
            "languages and do not use any other language, even if the DATA is "
            "written in a different one.\n"
        )
    return rules


def _facts_block(recommendation: dict, field: dict) -> str:
    """The ONLY source of truth the model may use, as compact JSON."""
    return json.dumps(
        {"field": field, "recommendation": recommendation},
        ensure_ascii=False,
        sort_keys=True,
        default=str,
    )


def _explain_user(recommendation: dict, field: dict) -> str:
    return (
        "DATA (the only facts you may use):\n"
        f"{_facts_block(recommendation, field)}\n\n"
        "Explain this recommendation to the farmer."
    )


def _answer_user(question: str, recommendation: dict, field: dict) -> str:
    return (
        "DATA (the only facts you may use):\n"
        f"{_facts_block(recommendation, field)}\n\n"
        f"The farmer's question (reply in its language): {question}"
    )


# --------------------------------------------------------------------------- #
# Live Gemini call — isolated behind a seam so it is easy to mock/replace
# --------------------------------------------------------------------------- #
def _api_key() -> str | None:
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")


def _get_client(api_key: str):
    """Construct the Gemini client. Patched out in tests (no network)."""
    from google import genai

    return genai.Client(api_key=api_key, http_options={"timeout": _TIMEOUT_MS})


def _call_model(system: str, user: str) -> str | None:
    """Return the model's text, or None on ANY failure (caller falls back).

    Never raises: a missing key, network/timeout error, blocked/safety response,
    or empty output all return None so the deterministic template takes over.
    """
    global _LAST_ERROR
    api_key = _api_key()
    if not api_key:
        _LAST_ERROR = "no_api_key"
        return None
    reason = None
    # One quick retry: free-tier flash-lite 503/504s are usually transient.
    for attempt in range(2):
        try:
            client = _get_client(api_key)
            resp = client.models.generate_content(
                model=_MODEL,
                contents=user,
                config={
                    "system_instruction": system,
                    "max_output_tokens": _MAX_TOKENS,
                    "temperature": 0.3,  # low -> faithful to the grounded data
                },
            )
            # resp.text can RAISE when a response is blocked/has no usable part.
            text = (getattr(resp, "text", None) or "").strip() or None
            if text:
                _LAST_ERROR = None
                return text
            reason = "empty_or_blocked_response"
            break  # an empty/blocked response won't improve on retry
        except Exception as e:  # must NEVER propagate — the demo can't hard-fail
            reason = f"{type(e).__name__}: {str(e)[:300]}"
            if attempt == 0:
                continue  # transient (503/504 etc.) — retry once
            break
    # Record WHY we fell back (for logs and /health), never leaking the key.
    if reason and api_key and api_key in reason:
        reason = reason.replace(api_key, "<redacted>")
    _LAST_ERROR = reason
    _log.warning("copilot: Gemini call failed (model=%s): %s", _MODEL, reason)
    return None


# --------------------------------------------------------------------------- #
# Public interface (signatures are the contract — do not change)
# --------------------------------------------------------------------------- #
def explain(recommendation: dict, field: dict, lang: str = "es") -> str:
    try:
        text = _call_model(_system_prompt(lang, "explain"), _explain_user(recommendation, field))
        if text:
            return text
    except Exception:
        pass
    return _fallback_explain(recommendation, field, lang)


def answer(question: str, recommendation: dict, field: dict, lang: str = "es") -> str:
    # Input-driven: the reply is written in the language the farmer typed the
    # question in. The live model mirrors it (see the "answer" system prompt);
    # the no-AI fallback detects it. `lang` is only the default when the
    # question is too short/ambiguous to tell.
    try:
        text = _call_model(_system_prompt(lang, "answer"), _answer_user(question, recommendation, field))
        if text:
            return text
    except Exception:
        pass
    return _fallback_answer(question, recommendation, field, lang)


def status() -> dict:
    """Non-secret copilot diagnostics for /health. NEVER returns the key itself.

    `key_format_ok` is a cheap sanity check: a Google AI Studio (Gemini Developer
    API) key starts with 'AIza' (classic) or 'AQ.' (newer AI Studio key format).
    A key that is set but fails this check is almost certainly the wrong
    credential type and the live call will 401 UNAUTHENTICATED — which is exactly
    the failure that otherwise hides behind the fallback.
    """
    key = _api_key()
    return {
        "provider": "google-gemini",
        "model": _MODEL,
        "has_key": bool(key),
        "key_format_ok": bool(key and (key.startswith("AIza") or key.startswith("AQ."))),
        "last_error": _LAST_ERROR,
    }
