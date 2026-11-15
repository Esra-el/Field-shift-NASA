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


def test_answer_detects_english_question_even_when_app_is_spanish(monkeypatch):
    # Farmer types English while the app toggle is Spanish -> answer in English.
    fake = _FakeClient(reply="ok")
    _with_fake(monkeypatch, fake)
    copilot.answer("When should I plant, and why?", REC, FIELD, lang="es")
    assert "reply in English" in _system_of(fake.calls[0])


def test_answer_detects_spanish_question_even_when_app_is_english(monkeypatch):
    fake = _FakeClient(reply="ok")
    _with_fake(monkeypatch, fake)
    copilot.answer("¿Cuándo debo sembrar el maíz?", REC, FIELD, lang="en")
    assert "reply in Spanish" in _system_of(fake.calls[0])


def test_answer_language_defaults_to_app_when_question_is_ambiguous(monkeypatch):
    fake = _FakeClient(reply="ok")
    _with_fake(monkeypatch, fake)
    copilot.answer("12345 ???", REC, FIELD, lang="en")   # no language signal
    assert "reply in English" in _system_of(fake.calls[0])


def test_detect_lang_unit():
    assert copilot._detect_lang("When should I plant maize?", "es") == "en"
    assert copilot._detect_lang("¿Cuánta lluvia cayó?", "en") == "es"
    assert copilot._detect_lang("cuando debo sembrar maiz", "en") == "es"   # no accents
    assert copilot._detect_lang("", "es") == "es"                           # empty -> default


def test_fallback_is_bilingual(monkeypatch):
    _no_keys(monkeypatch)
    es = copilot.explain(REC, FIELD, lang="es")
    en = copilot.explain(REC, FIELD, lang="en")
    assert "riesgo" in es.lower() and "sequía" in es.lower()   # Spanish
    assert "risk" in en.lower() and "drought" in en.lower()    # English
    assert es != en
