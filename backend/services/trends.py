from __future__ import annotations

import json
from statistics import mean, pstdev


TEXT_MARKERS = (
    "ttr_score",
    "mlu_score",
    "filler_density",
    "idea_density",
    "referential_cohesion",
    "semantic_coherence",
)

ACOUSTIC_MARKERS = (
    "words_per_minute",
    "average_pause_duration",
    "pause_frequency",
    "speech_tempo_variability",
    "vocal_energy",
    "pitch_variability",
    "jitter",
    "shimmer",
)

HIGHER_IS_BETTER = {"ttr_score", "mlu_score", "idea_density", "semantic_coherence", "vocal_energy"}
LOWER_IS_BETTER = {"filler_density", "referential_cohesion", "average_pause_duration", "pause_frequency", "jitter", "shimmer"}


def rolling_average(sessions: list[object], field: str, window: int = 7) -> float:
    rows = sessions[:window]
    if not rows:
        return 0.0
    return round(mean(float(getattr(item, field, 0.0) or 0.0) for item in rows), 3)


def baseline_deviation(current_value: float, baseline_value: float) -> float:
    if baseline_value == 0:
        return 0.0
    return round(((current_value - baseline_value) / abs(baseline_value)) * 100, 2)


def compute_baseline_deviation_map(current_session: object, baseline_markers: object) -> dict[str, float]:
    deviations: dict[str, float] = {}
    for field in TEXT_MARKERS + ACOUSTIC_MARKERS:
        deviations[field] = baseline_deviation(
            float(getattr(current_session, field, 0.0) or 0.0),
            float(getattr(baseline_markers, field, 0.0) or 0.0),
        )
    return deviations


def classify_deviation(percent_change: float) -> str:
    magnitude = abs(percent_change)
    if magnitude > 20:
        return "significant"
    if magnitude >= 10:
        return "moderate"
    return "stable"


def trend_velocity(sessions: list[object], field: str, window: int = 7) -> float:
    rows = list(reversed(sessions[:window]))
    if len(rows) < 2:
        return 0.0
    start = float(getattr(rows[0], field, 0.0) or 0.0)
    end = float(getattr(rows[-1], field, 0.0) or 0.0)
    return round((end - start) / max(1, len(rows) - 1), 3)


def marker_volatility(sessions: list[object], field: str, window: int = 7) -> float:
    rows = sessions[:window]
    if len(rows) < 2:
        return 0.0
    values = [float(getattr(item, field, 0.0) or 0.0) for item in rows]
    return round(pstdev(values), 3)


def detect_recovery(current_deviation: float, prior_deviation: float) -> bool:
    return abs(current_deviation) + 5 < abs(prior_deviation)


def derive_trend_direction(current_session: object, recent_sessions: list[object], baseline_markers: object) -> str:
    if not recent_sessions:
        return "stable"
    tracked_fields = ["ttr_score", "mlu_score", "idea_density", "semantic_coherence", "filler_density", "referential_cohesion"]
    score = 0
    for field in tracked_fields:
        current_value = float(getattr(current_session, field, 0.0) or 0.0)
        recent_average = rolling_average(recent_sessions, field)
        delta = current_value - recent_average
        if field in HIGHER_IS_BETTER:
            score += 1 if delta > 0 else -1 if delta < 0 else 0
        else:
            score += 1 if delta < 0 else -1 if delta > 0 else 0

    if score >= 2:
        return "improving"
    if score <= -2:
        return "declining"
    return "stable"


def detect_anomaly_markers(current_session: object, recent_sessions: list[object]) -> list[str]:
    anomalies: list[str] = []
    for field in TEXT_MARKERS + ACOUSTIC_MARKERS:
        volatility = marker_volatility(recent_sessions, field)
        current_value = float(getattr(current_session, field, 0.0) or 0.0)
        recent_average = rolling_average(recent_sessions, field)
        if volatility and abs(current_value - recent_average) > max(volatility * 2, abs(recent_average) * 0.2):
            anomalies.append(field)
    return anomalies


def weighted_longitudinal_risk(
    current_session: object,
    recent_sessions: list[object],
    baseline_markers: object,
    deviations: dict[str, float],
) -> float:
    risk = 35.0
    persistence_fields = ("ttr_score", "mlu_score", "filler_density", "idea_density", "referential_cohesion", "semantic_coherence")
    agreement_count = 0
    for field in persistence_fields:
        deviation = deviations.get(field, 0.0)
        classification = classify_deviation(deviation)
        direction_harmful = (
            deviation < 0 if field in HIGHER_IS_BETTER else deviation > 0
        )
        if classification == "significant" and direction_harmful:
            risk += 8
            agreement_count += 1
        elif classification == "moderate" and direction_harmful:
            risk += 4
            agreement_count += 1
        elif classification == "stable":
            risk -= 1

    if agreement_count >= 4:
        risk += 8
    elif agreement_count <= 1:
        risk -= 4

    volatility_penalty = sum(marker_volatility(recent_sessions, field) for field in ("ttr_score", "semantic_coherence", "filler_density"))
    risk += min(10, volatility_penalty * 3)

    pause_shift = deviations.get("average_pause_duration", 0.0) + deviations.get("pause_frequency", 0.0)
    tempo_shift = deviations.get("words_per_minute", 0.0)
    if pause_shift > 25:
        risk += 5
    if tempo_shift < -15:
        risk += 4

    if derive_trend_direction(current_session, recent_sessions, baseline_markers) == "improving":
        risk -= 6

    return round(max(0.0, min(100.0, risk)), 2)


def serialize_deviations(deviations: dict[str, float]) -> str:
    return json.dumps(deviations, sort_keys=True)
