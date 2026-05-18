from __future__ import annotations

import json
from datetime import datetime, timedelta
from statistics import mean
from typing import Iterable

from .schemas import AcousticMarkers, SessionScores


MARKER_FIELDS = (
    "ttr_score",
    "mlu_score",
    "filler_density",
    "idea_density",
    "referential_cohesion",
    "semantic_coherence",
    "composite_risk_score",
)

ACOUSTIC_FIELDS = (
    "words_per_minute",
    "average_pause_duration",
    "pause_frequency",
    "speech_tempo_variability",
    "vocal_energy",
    "pitch_variability",
    "jitter",
    "shimmer",
)


def average_scores(items: Iterable[object]) -> dict[str, float]:
    rows = list(items)
    if not rows:
        return {field: 0.0 for field in MARKER_FIELDS}
    return {
        field: round(mean(float(getattr(item, field)) for item in rows), 3)
        for field in MARKER_FIELDS
    }


def build_baseline_scores(items: Iterable[object]) -> SessionScores:
    values = average_scores(items)
    return SessionScores(**values)


def average_acoustic_scores(items: Iterable[object]) -> dict[str, float]:
    rows = list(items)
    if not rows:
        return {field: 0.0 for field in ACOUSTIC_FIELDS}
    return {
        field: round(mean(float(getattr(item, field, 0.0) or 0.0) for item in rows), 3)
        for field in ACOUSTIC_FIELDS
    }


def build_baseline_acoustics(items: Iterable[object]) -> AcousticMarkers:
    return AcousticMarkers(**average_acoustic_scores(items))


def calculate_trend_direction(current_avg: float | None, previous_avg: float | None) -> str:
    if current_avg is None or previous_avg is None:
        return "stable"
    delta = current_avg - previous_avg
    if delta > 3:
        return "declining"
    if delta < -3:
        return "improving"
    return "stable"


def first_name(full_name: str) -> str:
    return full_name.split()[0] if full_name.strip() else full_name


def days_since(dt: datetime | None) -> int | None:
    if dt is None:
        return None
    return max(0, (datetime.utcnow() - dt).days)


def date_window(reference: datetime, days: int) -> tuple[datetime, datetime]:
    return reference - timedelta(days=days), reference


def parse_json_text(value: str | None) -> dict:
    if not value:
        return {}
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return {}
