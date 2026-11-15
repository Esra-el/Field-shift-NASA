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
  * Simple, farmer-friendly language. Spanish by default ("es"), English on request.
  * MUST keep a deterministic fallback when no API key is set or the API errors —
    the live demo can never hard-fail on this call.

HOW IT WORKS
  One Gemini call (a fast, free-tier Flash model) turns the structured
  Recommendation into a short, farmer-friendly explanation. The model gets TWO
  guardrails:
    1. SYSTEM PROMPT (`config.system_instruction`) — locks it to EXPLAIN-ONLY:
       never invent a number, cite the NASA source behind each one, stay simple,
       end with a next action, and (for answers) refuse anything the data lacks.
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


# --------------------------------------------------------------------------- #
# Deterministic fallback (no API) — the live-demo safety net
# --------------------------------------------------------------------------- #
def _summary(recommendation: dict) -> tuple:
    rl = recommendation.get("risk_level", "?")
    rs = recommendation.get("risk_score", "?")
    wb = recommendation.get("water_budget", {}) or {}
    pt = recommendation.get("planting_timeline", {}) or {}
    action = str(pt.get("recommendation", "?")).replace("_", " ")
    return rl, rs, wb.get("explanation", ""), action


# The frontend is trilingual FR/EN/IT, plus Spanish for the pilot region, so the
# safety-net template must speak all four — otherwise a French or Italian user
# gets a Spanish fallback whenever the live Gemini call fails.
_FALLBACK_TEMPLATES = {
    "en": "Your field shows {rl} drought risk ({rs}/100). {wb} "
          "Recommendation: {ac}. (Data: NASA POWER, GPM IMERG, SMAP, MODIS NDVI.)",
    "es": "Su parcela muestra un riesgo de sequía {rl} ({rs}/100). {wb} "
          "Recomendación: {ac}. (Datos: NASA POWER, GPM IMERG, SMAP, MODIS NDVI.)",
    "fr": "Votre parcelle présente un risque de sécheresse {rl} ({rs}/100). {wb} "
          "Recommandation : {ac}. (Données : NASA POWER, GPM IMERG, SMAP, MODIS NDVI.)",
    "it": "Il tuo campo presenta un rischio di siccità {rl} ({rs}/100). {wb} "
          "Raccomandazione: {ac}. (Dati: NASA POWER, GPM IMERG, SMAP, MODIS NDVI.)",
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


def _fallback_explain(recommendation: dict, field: dict, lang: str = "es") -> str:
    rl, rs, wb_expl, action = _summary(recommendation)
    template = _FALLBACK_TEMPLATES.get(lang, _FALLBACK_TEMPLATES["es"])
    return template.format(rl=rl, rs=rs, wb=wb_expl, ac=action)


def _fallback_answer(question: str, recommendation: dict, field: dict, lang: str = "es") -> str:
    base = _fallback_explain(recommendation, field, lang)
    if _api_key():
        # Key present but the live call failed — give the clean answer, no noise.
        return base
    return base + _NO_KEY_HINT.get(lang, _NO_KEY_HINT["es"])


# --------------------------------------------------------------------------- #
# Prompt construction
# --------------------------------------------------------------------------- #
# Language detection for the chat. A light model (flash-lite) won't reliably
# switch languages from an instruction when the DATA context is heavily Spanish,
# so we decide the reply language in Python and hand the model a single, hard
# directive ("Write your entire reply in English/Spanish") — which it DOES follow.
# We only ever AUTO-detect Spanish vs English from the question text. French and
# Italian are taken from the app toggle (the `default`) and overridden ONLY on
# strong, distinctive evidence — never on a word Spanish merely shares with
# French/Italian ("que", "de", "la", "y"), which used to flip a French UI to
# Spanish (e.g. "Que dois-je faire ?" -> answered in Spanish).

# Characters ONLY Spanish uses (French/Italian never do): inverted marks + ñ.
# Plain accents (á é í ó ú ü) are shared with FR/IT, so they are NOT decisive.
_ES_ONLY_CHARS = set("ñ¿¡")

# Distinctive content words, deliberately chosen NOT to collide with French or
# Italian — so they are safe evidence even against a French/Italian UI.
_ES_WORDS = {
    "qué", "cuándo", "cuando", "cuánta", "cuanta", "cuánto", "cuanto",
    "cómo", "debo", "puedo", "siembro", "sembrar", "siembra", "lluvia",
    "suelo", "maíz", "maiz", "cosecha", "riesgo", "sequía", "sequia",
    "agua", "tierra", "necesito", "regar", "parcela",
}
_EN_WORDS = {
    "when", "should", "plant", "why", "how", "what", "the", "is", "are",
    "my", "rain", "water", "soil", "do", "can", "maize", "corn", "harvest",
    "risk", "drought", "wait", "will", "need", "i",
}


def _detect_lang(text: str, default: str) -> str:
    """Pick 'es'/'en' for the farmer's question, else keep `default`.

    For a French/Italian UI we keep that language unless the question is
    *clearly* Spanish or English — a Spanish-only character, or a solid
    word-count margin — so a shared word like French "Que dois-je…" stays French.
    """
    t = (text or "").lower()
    toks = set(re.findall(r"[a-zñáéíóúü]+", t))
    es = len(toks & _ES_WORDS)
    en = len(toks & _EN_WORDS)
    es_strong = any(ch in _ES_ONLY_CHARS for ch in t)

    if default in ("es", "en"):
        # Spanish/English UI: light touch — any clear lean (or a Spanish-only
        # character) sets the reply language.
        if es_strong:
            return "es"
        if en > es:
            return "en"
        if es > en:
            return "es"
        return default

    # French/Italian UI: override only on strong, unambiguous evidence.
    if es_strong or es >= en + 2:
        return "es"
    if en >= es + 2:
        return "en"
    return default


def _system_prompt(lang: str, mode: str) -> str:
    # The frontend is trilingual FR/EN/IT (plus Spanish for the pilot region);
    # answer in whatever language was asked for, defaulting to Spanish.
    reply_lang = {"en": "English", "es": "Spanish", "fr": "French", "it": "Italian"}.get(lang, "Spanish")
    rules = (
        "You are Field Shift's copilot. You help a rain-fed farmer in the Central "
        "American Dry Corridor understand a drought-planning recommendation.\n"
        "RULES:\n"
        "- EXPLAIN ONLY. Use ONLY the numbers and facts in the DATA the user gives "
        "you. Never invent a number, a date, or an agronomic fact.\n"
        "- When you mention a measurement, name the NASA source behind it: "
        f"{_NASA_SOURCES}.\n"
        "- Use simple, warm, farmer-friendly words. No jargon.\n"
        "- Be short and concrete, and finish with one clear next action.\n"
        f"- Write your entire reply in {reply_lang}.\n"
    )
    if mode == "answer":
        rules += (
            "- Answer using ONLY that DATA. If the question asks for something the "
            "DATA does not have that information, say so plainly and do not guess.\n"
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
        f"The farmer asks: {question}"
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
    # The chat replies in the language the farmer typed (falling back to the
    # app's language when the question's language is unclear).
    eff_lang = _detect_lang(question, lang)
    try:
        text = _call_model(_system_prompt(eff_lang, "answer"), _answer_user(question, recommendation, field))
        if text:
            return text
    except Exception:
        pass
    return _fallback_answer(question, recommendation, field, eff_lang)


def status() -> dict:
    """Non-secret copilot diagnostics for /health. NEVER returns the key itself.

    `key_format_ok` is a cheap sanity check: a Google AI Studio (Gemini Developer
    API) key starts with 'AIza'. A key that is set but fails this check is almost
    certainly the wrong credential type and the live call will 401 UNAUTHENTICATED
    — which is exactly the failure that otherwise hides behind the fallback.
    """
    key = _api_key()
    return {
        "provider": "google-gemini",
        "model": _MODEL,
        "has_key": bool(key),
        "key_format_ok": bool(key and key.startswith("AIza")),
        "last_error": _LAST_ERROR,
    }
