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
import os
import re

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


def _fallback_explain(recommendation: dict, field: dict, lang: str = "es") -> str:
    rl, rs, wb_expl, action = _summary(recommendation)
    if lang == "en":
        return (
            f"Your field shows {rl} drought risk ({rs}/100). {wb_expl} "
            f"Recommendation: {action}. "
            f"(Data: NASA POWER, GPM IMERG, SMAP, MODIS NDVI.)"
        )
    return (
        f"Su parcela muestra un riesgo de sequía {rl} ({rs}/100). {wb_expl} "
        f"Recomendación: {action}. "
        f"(Datos: NASA POWER, GPM IMERG, SMAP, MODIS NDVI.)"
    )


def _fallback_answer(question: str, recommendation: dict, field: dict, lang: str = "es") -> str:
    base = _fallback_explain(recommendation, field, lang)
    if lang == "en":
        return base + " [Copilot fallback — set GEMINI_API_KEY for full answers.]"
    return base + " [Copiloto básico — configure GEMINI_API_KEY para respuestas completas.]"


# --------------------------------------------------------------------------- #
# Prompt construction
# --------------------------------------------------------------------------- #
# Language detection for the chat. A light model (flash-lite) won't reliably
# switch languages from an instruction when the DATA context is heavily Spanish,
# so we decide the reply language in Python and hand the model a single, hard
# directive ("Write your entire reply in English/Spanish") — which it DOES follow.
_ES_CHARS = set("ñ¿¡áéíóúü")
_ES_WORDS = {
    "que", "qué", "cuando", "cuándo", "cuanta", "cuánta", "cuanto", "cuánto",
    "como", "cómo", "por", "para", "debo", "puedo", "siembro", "sembrar",
    "lluvia", "agua", "suelo", "maíz", "maiz", "cosecha", "riesgo", "sequía",
    "sequia", "mi", "el", "la", "los", "las", "de", "y", "no", "sí",
}
_EN_WORDS = {
    "when", "should", "plant", "why", "how", "what", "the", "is", "are", "my",
    "rain", "water", "soil", "i", "to", "do", "can", "maize", "corn", "harvest",
    "risk", "drought", "wait", "and", "of", "will",
}


def _detect_lang(text: str, default: str) -> str:
    """Return 'es' or 'en' for the farmer's question; fall back to `default`."""
    t = (text or "").lower()
    if any(ch in _ES_CHARS for ch in t):
        return "es"
    toks = set(re.findall(r"[a-záéíóúñ]+", t))
    es, en = len(toks & _ES_WORDS), len(toks & _EN_WORDS)
    if en > es:
        return "en"
    if es > en:
        return "es"
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
    api_key = _api_key()
    if not api_key:
        return None
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
            return (getattr(resp, "text", None) or "").strip() or None
        except Exception:
            # Transient error -> retry once; still failing -> caller falls back.
            if attempt == 0:
                continue
            return None
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
