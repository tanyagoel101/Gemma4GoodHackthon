from __future__ import annotations

from statistics import mean

from backend.services.alerts import generate_alerts
from backend.services.trends import (
    HIGHER_IS_BETTER,
    classify_deviation,
    compute_baseline_deviation_map,
    derive_trend_direction,
    rolling_average,
)


MARKER_LABELS = {
    "ttr_score": "vocabulary variety",
    "mlu_score": "sentence complexity",
    "filler_density": "filler phrases",
    "idea_density": "idea density",
    "referential_cohesion": "specific naming",
    "semantic_coherence": "overall coherence",
    "words_per_minute": "speech pace",
    "average_pause_duration": "pause length",
    "pause_frequency": "pause frequency",
    "pitch_variability": "pitch variety",
}


def _confidence_from_data(recent_sessions: list[object], notable_changes: list[str]) -> str:
    if len(recent_sessions) >= 7 and len(notable_changes) >= 2:
        return "high"
    if len(recent_sessions) >= 4:
        return "moderate"
    return "low"


def _severity_from_notable_changes(notable_changes: list[str]) -> str:
    if len(notable_changes) >= 3:
        return "high"
    if notable_changes:
        return "moderate"
    return "low"


def generate_session_insights(current_session: object, baseline: object, recent_sessions: list[object]) -> dict:
    deviations = compute_baseline_deviation_map(current_session, baseline)
    trend_direction = derive_trend_direction(current_session, recent_sessions, baseline)
    notable_changes: list[str] = []
    stable_markers: list[str] = []
    actionable_observations: list[str] = []

    for field in ("ttr_score", "mlu_score", "filler_density", "idea_density", "referential_cohesion", "semantic_coherence", "words_per_minute", "average_pause_duration", "pause_frequency"):
        label = MARKER_LABELS[field]
        deviation = deviations.get(field, 0.0)
        change_level = classify_deviation(deviation)
        if change_level == "stable":
            stable_markers.append(label)
            continue

        harmful_direction = deviation < 0 if field in HIGHER_IS_BETTER else deviation > 0
        if harmful_direction:
            descriptor = "gradually shifted" if abs(deviation) < 25 else "moved more noticeably"
            notable_changes.append(f"{label.title()} has {descriptor} compared with baseline.")
        else:
            actionable_observations.append(f"{label.title()} looks a bit stronger than the earlier baseline pattern.")

    if not actionable_observations and trend_direction == "improving":
        actionable_observations.append("Several markers are moving back toward the personal baseline.")
    if not actionable_observations and trend_direction == "stable":
        actionable_observations.append("Most markers remain within the expected day-to-day range.")

    confidence = _confidence_from_data(recent_sessions, notable_changes)
    severity = _severity_from_notable_changes(notable_changes)
    alerts = generate_alerts(deviations, trend_direction, confidence, notable_changes)

    caregiver_summary_parts = []
    if notable_changes:
        caregiver_summary_parts.append(notable_changes[0])
    if stable_markers:
        caregiver_summary_parts.append(f"Stable areas include {', '.join(stable_markers[:3])}.")
    caregiver_summary_parts.append(
        "This is meant to help you notice patterns over time, not to label any single recording."
    )

    clinician_summary_parts = [
        f"Recent longitudinal pattern is {trend_direction} relative to baseline and the rolling 7-session average."
    ]
    if notable_changes:
        clinician_summary_parts.append("Notable shifts: " + " ".join(notable_changes[:3]))
    if actionable_observations:
        clinician_summary_parts.append("Observations: " + " ".join(actionable_observations[:2]))

    return {
        "caregiver_summary": " ".join(caregiver_summary_parts).strip(),
        "clinician_summary": " ".join(clinician_summary_parts).strip(),
        "notable_changes": notable_changes,
        "stable_markers": stable_markers[:4],
        "actionable_observations": actionable_observations[:3],
        "severity": severity,
        "confidence": confidence,
        "trend_direction": trend_direction,
        "baseline_deviation": deviations,
        "alerts": alerts,
    }

