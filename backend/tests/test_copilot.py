"""Tests for the explainable AI copilot (app/copilot.py).

Provider: Google Gemini (free tier). HARD REQUIREMENT: these pass with NO API
key and NO network. The live Gemini path is never hit here — we either exercise
the deterministic fallback (no key) or swap in a fake Gemini client via the
`_get_client` seam. The copilot must NEVER raise and must NEVER hard-fail the
live demo, so every path returns a usable string.
"""
import json

from app import copilot

# A realistic Recommendation (app/schemas.py shape) + the field it describes.
REC = {
    "risk_score": 72,
    "risk_level": "high",
    "water_budget": {
        "status": "not_enough_water",
        "crop_water_need_mm": 450.0,
        "available_water_mm": 300.0,
        "deficit_mm": 150.0,
        "explanation": "La lluvia esta 40% por debajo de lo normal en los ultimos 60 dias.",
    },
    "planting_timeline": {
        "recommendation": "wait",
        "best_window": "2026-11-20 to 2026-11-30",
        "reason": "La humedad del suelo aun es muy baja para germinar maiz.",
    },
    "rotations": [
        {
            "type": "safest",
            "name": "Frijol -> Sorgo -> Cultivo de cobertura",
            "water_saving": "high",
            "soil_benefit": "high",
            "risk": "low",
            "reason": "Usa menos agua y protege el suelo.",
        }
    ],
    "nasa_indicators": {
        "rainfall_60d_mm": 90.0,
        "rainfall_normal_mm": 150.0,
        "soil_moisture": 0.18,
        "ndvi_trend": -0.05,
        "solar_radiation": 21.0,
        "evapotranspiration": 5.2,
    },
    "ai_explanation": "",
    "data_mode": "mock",
}

FIELD = {
    "latitude": 14.8,
    "longitude": -90.5,
    "crop": "maize",
    "soil_type": "sandy_loam",
    "irrigation": False,
    "priority": "save_water",
}


# --------------------------------------------------------------------------- #
# Fake Gemini client (no network) injected through copilot._get_client.
# Mirrors google-genai: client.models.generate_content(...) -> resp.text
# --------------------------------------------------------------------------- #
class _FakeResponse:
    def __init__(self, text, raise_on_text=False):
        self._text = text
        self._raise = raise_on_text

    @property
    def text(self):
        # google-genai raises when a response has no usable Part (e.g. blocked).
        if self._raise:
            raise ValueError("no valid Part (blocked / safety)")
        return self._text


class _FakeModels:
    def __init__(self, parent):
        self._parent = parent

    def generate_content(self, **kwargs):
        self._parent.calls.append(kwargs)
        if self._parent.raise_exc:
            raise RuntimeError("simulated API failure / timeout")
        return _FakeResponse(self._parent.reply, self._parent.raise_on_text)


class _FakeClient:
    def __init__(self, reply="texto del copiloto", raise_exc=False, raise_on_text=False):
        self.reply = reply
        self.raise_exc = raise_exc
        self.raise_on_text = raise_on_text
        self.calls = []
        self.models = _FakeModels(self)


def _no_keys(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)


def _with_fake(monkeypatch, fake):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(copilot, "_get_client", lambda api_key: fake)


def _system_of(kwargs):
    # System prompt is carried in the generate_content `config`.
    cfg = kwargs["config"]
    return cfg["system_instruction"] if isinstance(cfg, dict) else cfg.system_instruction


def _dump(kwargs):
    """Serialize request kwargs for substring grounding assertions (keep unicode)."""
    return json.dumps(kwargs, default=str, ensure_ascii=False)


# --------------------------------------------------------------------------- #
# Fallback path — NO API key (the live-demo safety net)
# --------------------------------------------------------------------------- #
def test_explain_fallback_no_key_es(monkeypatch):
    _no_keys(monkeypatch)
    out = copilot.explain(REC, FIELD, lang="es")
    assert isinstance(out, str) and out.strip()
    assert "NASA POWER" in out            # cites the data source
    assert "riesgo" in out.lower()        # Spanish by default


def test_explain_fallback_no_key_en(monkeypatch):
    _no_keys(monkeypatch)
    out = copilot.explain(REC, FIELD, lang="en")
    assert isinstance(out, str) and out.strip()
    assert "NASA POWER" in out
    assert "risk" in out.lower()          # English on request


def test_answer_fallback_no_key(monkeypatch):
    _no_keys(monkeypatch)
    out = copilot.answer("¿Cuándo debo sembrar?", REC, FIELD, lang="es")
    assert isinstance(out, str) and out.strip()


# --------------------------------------------------------------------------- #
# Live path (mocked) — system prompt + grounding wiring
# --------------------------------------------------------------------------- #
def test_explain_uses_model_when_key_present(monkeypatch):
    fake = _FakeClient(reply="Su parcela tiene riesgo alto; espere a sembrar.")
    _with_fake(monkeypatch, fake)

    out = copilot.explain(REC, FIELD, lang="es")
    assert out == "Su parcela tiene riesgo alto; espere a sembrar."
    assert len(fake.calls) == 1

    kwargs = fake.calls[0]
    assert "gemini" in kwargs["model"].lower()        # Google Gemini (free tier)
    cfg = kwargs["config"]
    max_out = cfg["max_output_tokens"] if isinstance(cfg, dict) else cfg.max_output_tokens
    assert max_out <= 1024                            # short explanation, sane latency
    # System prompt locks it to explain-only and names the NASA sources.
    system = _system_of(kwargs)
    assert "SMAP" in system
    assert "NASA POWER" in system
    # Grounding: the recommendation's own numbers are the only facts supplied.
    payload = _dump(kwargs)
    assert "72" in payload                            # risk_score passed through
    assert "not_enough_water" in payload              # water status passed through


def test_answer_is_grounded_in_request(monkeypatch):
    fake = _FakeClient(reply="Segun los datos, la lluvia fue 90 mm.")
    _with_fake(monkeypatch, fake)

    q = "¿Cuánta lluvia cayó en los últimos 60 días?"
    out = copilot.answer(q, REC, FIELD, lang="es")
    assert out == "Segun los datos, la lluvia fue 90 mm."

    kwargs = fake.calls[0]
    payload = _dump(kwargs)
    assert q in payload                               # the farmer's question is sent
    assert "90" in payload                            # rainfall fact available to ground on
    # Guardrail: out-of-data questions must be declined, not guessed.
    assert "does not have that information" in _system_of(kwargs)


# --------------------------------------------------------------------------- #
# Robustness — must NEVER raise, must always return a usable string
# --------------------------------------------------------------------------- #
def test_explain_never_raises_when_client_throws(monkeypatch):
    fake = _FakeClient(raise_exc=True)
    _with_fake(monkeypatch, fake)

    out = copilot.explain(REC, FIELD, lang="es")
    assert isinstance(out, str) and out.strip()       # fell back, no exception
    assert "NASA POWER" in out


def test_answer_never_raises_when_client_throws(monkeypatch):
    fake = _FakeClient(raise_exc=True)
    _with_fake(monkeypatch, fake)

    out = copilot.answer("cualquier cosa?", REC, FIELD, lang="en")
    assert isinstance(out, str) and out.strip()


def test_explain_falls_back_on_empty_model_text(monkeypatch):
    fake = _FakeClient(reply="   ")                   # model returned nothing usable
    _with_fake(monkeypatch, fake)

    out = copilot.explain(REC, FIELD, lang="es")
    assert "NASA POWER" in out                        # degraded to template


def test_explain_falls_back_on_blocked_response(monkeypatch):
    # Gemini signals a blocked/safety response by raising when .text is read.
    fake = _FakeClient(raise_on_text=True)
    _with_fake(monkeypatch, fake)

    out = copilot.explain(REC, FIELD, lang="en")
    assert isinstance(out, str) and out.strip()
    assert "NASA POWER" in out


# --------------------------------------------------------------------------- #
# Bilingual — English AND Spanish, in both the live prompt and the fallback
# --------------------------------------------------------------------------- #
def test_explain_prompt_is_english_when_requested(monkeypatch):
    fake = _FakeClient(reply="ok")
    _with_fake(monkeypatch, fake)
    copilot.explain(REC, FIELD, lang="en")
    assert "English" in _system_of(fake.calls[0])


def test_explain_prompt_is_spanish_by_default(monkeypatch):
    fake = _FakeClient(reply="ok")
    _with_fake(monkeypatch, fake)
    copilot.explain(REC, FIELD)                       # default lang="es"
    assert "Spanish" in _system_of(fake.calls[0])


# The reply language is the app's SELECTED language (the toggle) by DEFAULT; the
# farmer can override it inside the question ("answer in Italian"), which the
# model honors. No question-language guessing.
def test_answer_prompt_defaults_to_app_language(monkeypatch):
    fake = _FakeClient(reply="ok")
    _with_fake(monkeypatch, fake)
    # English question but the app toggle is French -> the DEFAULT reply is French
    # (the toggle), not driven by the question's language.
    copilot.answer("When should I plant, and why?", REC, FIELD, lang="fr")
    sysp = _system_of(fake.calls[0])
    assert "French by DEFAULT" in sysp
    assert "English by DEFAULT" not in sysp


def test_answer_prompt_allows_explicit_language_override(monkeypatch):
    fake = _FakeClient(reply="ok")
    _with_fake(monkeypatch, fake)
    copilot.answer("Answer in Italian please", REC, FIELD, lang="fr")
    sysp = _system_of(fake.calls[0]).lower()
    # The override instruction is present so the model can switch on request.
    assert "answer in italian" in sysp and "reply in another language" in sysp


def test_answer_prompt_stays_conversational_not_a_report(monkeypatch):
    # Greetings, small talk, a language-switch request, etc. must NOT trigger a
    # full recommendation dump — the copilot stays a chat assistant and asks.
    fake = _FakeClient(reply="ok")
    _with_fake(monkeypatch, fake)
    copilot.answer("I need help", REC, FIELD, lang="en")
    sysp = _system_of(fake.calls[0]).lower()
    assert "chat assistant, not a report" in sysp
    assert "no risk score" in sysp          # a greeting carries NO field data
    assert "1-3 sentences" in sysp          # every reply stays short


def test_answer_fallback_uses_app_language_not_question(monkeypatch):
    # No key -> rule-based fallback, in the app's SELECTED language, regardless of
    # the language the question happens to be typed in.
    _no_keys(monkeypatch)
    out = copilot.answer("When should I plant?", REC, FIELD, lang="es").lower()
    assert "riesgo" in out              # Spanish (the toggle), not the English question
    assert "drought risk" not in out


def test_answer_fallback_french_toggle(monkeypatch):
    _no_keys(monkeypatch)
    out = copilot.answer("When should I plant?", REC, FIELD, lang="fr").lower()
    assert "sécheresse" in out          # French (the toggle)
    assert "drought risk" not in out


def test_answer_fallback_italian_toggle(monkeypatch):
    _no_keys(monkeypatch)
    out = copilot.answer("When should I plant?", REC, FIELD, lang="it").lower()
    assert "siccità" in out             # Italian (the toggle)


def test_answer_fallback_short_question_uses_ui_language(monkeypatch):
    # Too short / no signal -> fall back to the app's chosen language.
    _no_keys(monkeypatch)
    out = copilot.answer("ok?", REC, FIELD, lang="fr").lower()
    assert "sécheresse" in out


def test_answer_prompt_forbids_mixing_languages(monkeypatch):
    fake = _FakeClient(reply="ok")
    _with_fake(monkeypatch, fake)
    copilot.answer("Que dois-je faire ?", REC, FIELD, lang="fr")
    assert "Do NOT mix languages" in _system_of(fake.calls[0])


# --------------------------------------------------------------------------- #
# Fallback is genuinely multilingual — a French/Italian UI never degrades to
# Spanish text when the live call is unavailable.
# --------------------------------------------------------------------------- #
def test_fallback_explain_speaks_french_and_italian(monkeypatch):
    _no_keys(monkeypatch)
    fr = copilot.explain(REC, FIELD, lang="fr")
    it = copilot.explain(REC, FIELD, lang="it")
    assert "sécheresse" in fr.lower()        # French, not Spanish
    assert "riesgo" not in fr.lower()
    assert "siccità" in it.lower()           # Italian, not Spanish
    assert "NASA POWER" in fr and "NASA POWER" in it


def test_fallback_answer_with_key_present_has_no_key_hint(monkeypatch):
    # Key IS set but the live call fails -> clean rule-based answer, and it must
    # NOT tell the user to configure a key they already configured.
    fake = _FakeClient(raise_exc=True)
    _with_fake(monkeypatch, fake)
    out = copilot.answer("Que dois-je faire ?", REC, FIELD, lang="fr")
    assert isinstance(out, str) and out.strip()
    assert "GEMINI_API_KEY" not in out
    assert "sécheresse" in out.lower()       # answered in French


def test_fallback_answer_no_key_hints_in_right_language(monkeypatch):
    _no_keys(monkeypatch)
    out = copilot.answer("Que dois-je faire ?", REC, FIELD, lang="fr")
    assert "GEMINI_API_KEY" in out           # dev hint only when no key at all
    assert "sécheresse" in out.lower()       # still French


# --------------------------------------------------------------------------- #
# Non-secret diagnostics for /health — must never leak the key.
# --------------------------------------------------------------------------- #
def test_status_reports_diagnostics_without_leaking_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyFAKEfakefakefakefakefakefake12345")
    st = copilot.status()
    assert st["has_key"] is True
    assert st["key_format_ok"] is True       # starts with AIza
    assert "gemini" in st["model"].lower()
    # The key value itself must never appear anywhere in the status payload.
    assert "AIzaSyFAKEfakefakefakefakefakefake12345" not in json.dumps(st)


def test_status_flags_wrong_format_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "not-an-aistudio-key.abc-123")
    st = copilot.status()
    assert st["has_key"] is True
    assert st["key_format_ok"] is False      # wrong credential type -> will 401


def test_status_accepts_new_aq_key_format(monkeypatch):
    # Newer Google AI Studio keys start with 'AQ.' — must be accepted as valid.
    monkeypatch.setenv("GEMINI_API_KEY", "AQ.Ab8RNfakefakefakefakefakefakefakefake")
    st = copilot.status()
    assert st["has_key"] is True
    assert st["key_format_ok"] is True


def test_fallback_is_bilingual(monkeypatch):
    _no_keys(monkeypatch)
    es = copilot.explain(REC, FIELD, lang="es")
    en = copilot.explain(REC, FIELD, lang="en")
    assert "riesgo" in es.lower() and "sequía" in es.lower()   # Spanish
    assert "risk" in en.lower() and "drought" in en.lower()    # English
    assert es != en
