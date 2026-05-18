from __future__ import annotations

import json
import logging
from datetime import datetime
from statistics import mean
from urllib.parse import urljoin

from fastapi import HTTPException, status
import httpx

from backend.config import get_settings
from backend.utils import first_name


settings = get_settings()
logger = logging.getLogger("uvicorn.error")
OLLAMA_CHAT_TIMEOUT_SECONDS = 360.0


EXTRACTION_PROMPT = """Analyze the following speech transcript and extract these six neurolinguistic markers:

1. ttr_score: Type-Token Ratio. Calculate: unique_words / total_words. Value between 0-1.
   Higher = more vocabulary diversity (healthy). Lower = vocabulary shrinkage (concerning).

2. mlu_score: Mean Length of Utterance. Calculate: total_words / number_of_sentences.
   This is average words per sentence. Normal adult range: 10-20. Declining = shorter sentences.

3. filler_density: Count filler words (um, uh, like, you know, sort of, kind of, basically,
   actually used as filler, I mean, right?) per 100 words. Higher = more cognitive load.

4. idea_density: Estimate propositional content — the number of discrete ideas or facts
   per 10 words. Score 0-1. Higher = more information-dense speech. Declining with dementia.

5. referential_cohesion: Calculate ratio of pronouns (he, she, it, they, this, that,
   these, those) to total nouns. High ratio = vague references, difficulty naming. Score 0-1.

6. semantic_coherence: Rate on a scale of 1-10 how coherent and on-topic the narrative
   is. Does it stay on topic? Are transitions logical? Does it reach a conclusion?
   10 = perfectly coherent, 1 = fragmented/incoherent.

7. gemma_summary: Write one sentence (max 30 words) describing the speech characteristics
   in plain, non-alarming language suitable for a family caregiver.

8. clinical_notes: Write 2-3 sentences of clinical observations suitable for a GP.
   Note any specific linguistic patterns of concern or health.

Transcript:
\"\"\"
{transcript}
\"\"\"

Respond ONLY with this JSON structure:
{{
  "ttr_score": 0.0,
  "mlu_score": 0.0,
  "filler_density": 0.0,
  "idea_density": 0.0,
  "referential_cohesion": 0.0,
  "semantic_coherence": 0.0,
  "gemma_summary": "",
  "clinical_notes": ""
}}
"""


STRICTER_JSON_SUFFIX = "\nReturn only compact valid JSON. Do not include markdown fences or commentary."


def _model_matches(candidate: str, requested: str) -> bool:
    candidate = candidate.strip()
    requested = requested.strip()
    if candidate == requested:
        return True
    if candidate.startswith(f"{requested}:"):
        return True
    if requested.startswith(f"{candidate}:"):
        return True
    return False


async def _chat_with_fallback(messages: list[dict[str, str]], format: str | None = None) -> str:
    models_to_try = [settings.ollama_model]
    if settings.ollama_fallback_model not in models_to_try:
        models_to_try.append(settings.ollama_fallback_model)

    last_error: Exception | None = None
    timeout_error: httpx.TimeoutException | None = None
    for model_name in models_to_try:
        try:
            logger.info("Calling Ollama chat model=%s format=%s", model_name, format or "default")
            timeout = httpx.Timeout(OLLAMA_CHAT_TIMEOUT_SECONDS, connect=10.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    urljoin(settings.ollama_base_url, "/api/chat"),
                    json={
                        "model": model_name,
                        "messages": messages,
                        "stream": False,
                        **({"format": format} if format else {}),
                    },
                )
                response.raise_for_status()
                payload = response.json()
                content = payload.get("message", {}).get("content", "")
                if content:
                    logger.info("Ollama chat complete model=%s response_chars=%s", model_name, len(content))
                    return content
                raise ValueError("Ollama response did not include message content.")
        except httpx.TimeoutException as exc:
            last_error = exc
            timeout_error = exc
            logger.warning("Ollama chat timed out for model=%s after %.0fs", model_name, OLLAMA_CHAT_TIMEOUT_SECONDS)
        except httpx.HTTPStatusError as exc:
            last_error = exc
            logger.warning(
                "Ollama chat returned status=%s for model=%s",
                exc.response.status_code,
                model_name,
            )
        except Exception as exc:  # noqa: BLE001
            last_error = exc

    if timeout_error is not None:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=(
                "Gemma took too long to respond locally. Try a shorter recording first, "
                "or retry once Ollama has warmed up."
            ),
        ) from timeout_error

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=(
            f"VoiceTrace could not complete the Ollama request at {settings.ollama_base_url} with model "
            f"'{settings.ollama_model}'. Please make sure Ollama is running and the model is available."
        ),
    ) from last_error


def calculate_composite_risk_score(markers: dict[str, float]) -> float:
    risk = 50.0
    if markers["ttr_score"] < 0.4:
        risk += 15
    elif markers["ttr_score"] > 0.55:
        risk -= 10

    if markers["mlu_score"] < 8:
        risk += 10
    elif markers["mlu_score"] > 14:
        risk -= 6

    if markers["filler_density"] > 8:
        risk += 10
    elif markers["filler_density"] < 4:
        risk -= 5

    if markers["idea_density"] < 0.3:
        risk += 10
    elif markers["idea_density"] > 0.55:
        risk -= 8

    if markers["referential_cohesion"] > 0.6:
        risk += 10
    elif markers["referential_cohesion"] < 0.3:
        risk -= 5

    if markers["semantic_coherence"] < 6:
        risk += 5
    elif markers["semantic_coherence"] > 8:
        risk -= 6

    return round(max(0.0, min(100.0, risk)), 2)


def _parse_marker_json(raw_text: str) -> dict:
    data = json.loads(raw_text)
    markers = {
        "ttr_score": float(data["ttr_score"]),
        "mlu_score": float(data["mlu_score"]),
        "filler_density": float(data["filler_density"]),
        "idea_density": float(data["idea_density"]),
        "referential_cohesion": float(data["referential_cohesion"]),
        "semantic_coherence": float(data["semantic_coherence"]),
        "gemma_summary": str(data["gemma_summary"]).strip(),
        "clinical_notes": str(data["clinical_notes"]).strip(),
    }
    markers["composite_risk_score"] = calculate_composite_risk_score(markers)
    return markers


async def extract_linguistic_markers(transcript: str) -> dict:
    messages = [
        {
            "role": "system",
            "content": (
                "You are a neurolinguistic analysis assistant. You extract clinically validated "
                "speech biomarkers from transcripts to support early cognitive decline monitoring. "
                "You always respond with valid JSON only. No preamble, no explanation, no markdown."
            ),
        },
        {"role": "user", "content": EXTRACTION_PROMPT.format(transcript=transcript)},
    ]
    raw_text = await _chat_with_fallback(messages, format="json")
    try:
        return _parse_marker_json(raw_text)
    except Exception:  # noqa: BLE001
        retry_messages = messages[:-1] + [
            {"role": "user", "content": EXTRACTION_PROMPT.format(transcript=transcript) + STRICTER_JSON_SUFFIX}
        ]
        retry_text = await _chat_with_fallback(retry_messages, format="json")
        try:
            return _parse_marker_json(retry_text)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Gemma returned an unreadable analysis payload. Please try again.",
            ) from exc


async def generate_weekly_summary(sessions: list[dict], patient_name: str) -> str:
    payload = json.dumps(sessions[-7:], default=str)
    messages = [
        {
            "role": "system",
            "content": "You write warm, plain-language caregiver summaries. Be calm, specific, and non-alarming.",
        },
        {
            "role": "user",
            "content": (
                f"Using the last 7 sessions for {first_name(patient_name)}, write exactly 3 sentences. "
                "Reference any significant change from earlier in the week to later in the week. "
                "Avoid diagnostic language.\n\n"
                f"Sessions JSON:\n{payload}"
            ),
        },
    ]
    return (await _chat_with_fallback(messages)).strip()


async def generate_preappointment_brief(sessions: list[dict], patient: dict) -> str:
    payload = json.dumps(sessions, default=str)
    messages = [
        {
            "role": "system",
            "content": "You create concise structured clinical support briefs from longitudinal linguistic data.",
        },
        {
            "role": "user",
            "content": (
                "Generate a structured clinical pre-appointment brief in this exact format:\n\n"
                "PATIENT LINGUISTIC HEALTH BRIEF\n"
                "Patient: [name], [age]\n"
                "Period: [date range]\n"
                "Prepared by: VoiceTrace AI (for clinical support only — not a diagnostic tool)\n\n"
                "TREND SUMMARY\n"
                "[2-3 sentences on overall trajectory]\n\n"
                "KEY FINDINGS\n"
                "- [marker name]: [trend description with specific values]\n"
                "- [repeat for each of the 6 markers]\n\n"
                "AREAS OF CONCERN\n"
                "[Any markers showing consistent decline over the period]\n\n"
                "SUGGESTED DISCUSSION POINTS\n"
                "[2-3 conversation prompts the GP might raise during the appointment]\n\n"
                "BASELINE COMPARISON\n"
                "[How current scores compare to the patient's own personal baseline (first 2 weeks of recordings)]\n\n"
                f"Patient JSON:\n{json.dumps(patient, default=str)}\n\n"
                f"Sessions JSON:\n{payload}"
            ),
        },
    ]
    return (await _chat_with_fallback(messages)).strip()


async def generate_referral_letter(patient: dict, sessions: list[dict], referring_gp: str) -> str:
    payload = json.dumps(sessions, default=str)
    messages = [
        {
            "role": "system",
            "content": "You draft polished medical referral letters from structured patient trend data.",
        },
        {
            "role": "user",
            "content": (
                "Generate a structured neurology referral letter from longitudinal speech-monitoring data. "
                "Use a professional medical tone. Include patient demographics, duration of monitoring, "
                "key marker trends with specific numbers, rate of change, and the clinical reasoning for referral. "
                "End with this exact disclaimer: "
                "\"Generated by VoiceTrace AI to assist clinical documentation. Requires physician review before sending.\"\n\n"
                f"Referring GP: {referring_gp}\n"
                f"Patient JSON:\n{json.dumps(patient, default=str)}\n\n"
                f"Sessions JSON:\n{payload}"
            ),
        },
    ]
    return (await _chat_with_fallback(messages)).strip()


async def check_ollama_health() -> tuple[str, str]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(urljoin(settings.ollama_base_url, "/api/tags"))
            response.raise_for_status()
            models = response.json()
    except httpx.HTTPError as exc:
        return "unreachable", str(exc)
    except Exception as exc:  # noqa: BLE001
        return "unreachable", str(exc)

    available = []
    for model in models.get("models", []):
        name = model.get("name", "")
        if name:
            available.append(name)
    for name in available:
        if _model_matches(name, settings.ollama_model):
            return "ready", name
    for name in available:
        if _model_matches(name, settings.ollama_fallback_model):
            return "fallback", name
    return "missing_model", ", ".join(filter(None, available)) or "no models reported"


def build_session_payloads(sessions: list[object]) -> list[dict]:
    payloads = []
    for session in sessions:
        payloads.append(
            {
                "recorded_at": getattr(session, "recorded_at"),
                "ttr_score": getattr(session, "ttr_score"),
                "mlu_score": getattr(session, "mlu_score"),
                "filler_density": getattr(session, "filler_density"),
                "idea_density": getattr(session, "idea_density"),
                "referential_cohesion": getattr(session, "referential_cohesion"),
                "semantic_coherence": getattr(session, "semantic_coherence"),
                "composite_risk_score": getattr(session, "composite_risk_score"),
                "gemma_summary": getattr(session, "gemma_summary"),
            }
        )
    return payloads


def summarize_range(sessions: list[object]) -> str:
    if not sessions:
        return "No sessions available"
    scores = [float(session.composite_risk_score) for session in sessions]
    return (
        f"{sessions[-1].recorded_at:%Y-%m-%d} to {sessions[0].recorded_at:%Y-%m-%d}; "
        f"average composite {mean(scores):.1f}"
    )
