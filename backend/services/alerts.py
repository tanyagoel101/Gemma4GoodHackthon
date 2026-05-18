from __future__ import annotations

from backend.services.trends import classify_deviation


def generate_alerts(
    deviations: dict[str, float],
    trend_direction: str,
    confidence: str,
    notable_changes: list[str],
) -> list[str]:
    alerts: list[str] = []
    if trend_direction == "declining" and notable_changes:
        alerts.append("A larger-than-usual change was detected compared to the usual pattern.")
    if trend_direction == "stable":
        alerts.append("Speech patterns remain fairly steady this week.")
    if classify_deviation(deviations.get("ttr_score", 0.0)) == "significant":
        alerts.append("Vocabulary diversity has shifted consistently from baseline across recent sessions.")
    if confidence == "low":
        alerts.append("Confidence is lower right now because the recent data is limited or more variable.")
    return alerts[:3]

