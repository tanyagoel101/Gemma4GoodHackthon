from __future__ import annotations

from statistics import mean


def _avg(items: list[float]) -> float:
    return round(mean(items), 3) if items else 0.0


def generate_correlations(events: list[object], sessions: list[object]) -> dict:
    findings: list[str] = []
    associations: list[dict[str, str | float]] = []
    if len(events) < 2 or len(sessions) < 4:
        return {
            "findings": ["More event and recording history is needed before VoiceTrace can describe meaningful associations."],
            "strongest_associations": [],
            "confidence": "low",
            "note": "These observations describe patterns that may coincide with voice changes. They do not imply causation.",
        }

    sleep_low_scores = []
    sleep_high_scores = []
    social_high_coherence = []
    social_low_coherence = []
    for event in events:
        matching_sessions = [session for session in sessions if session.recorded_at.date() >= event.event_date]
        session = matching_sessions[0] if matching_sessions else None
        if not session:
            continue
        if event.sleep_quality <= 2:
            sleep_low_scores.append(float(session.filler_density))
        if event.sleep_quality >= 4:
            sleep_high_scores.append(float(session.filler_density))
        if event.social_activity >= 4:
            social_high_coherence.append(float(session.semantic_coherence))
        if event.social_activity <= 2:
            social_low_coherence.append(float(session.semantic_coherence))

    if sleep_low_scores and sleep_high_scores and _avg(sleep_low_scores) > _avg(sleep_high_scores):
        findings.append("Higher filler density frequently followed lower sleep-quality entries.")
        associations.append({"event": "sleep quality", "marker": "filler density", "difference": round(_avg(sleep_low_scores) - _avg(sleep_high_scores), 2)})
    if social_high_coherence and social_low_coherence and _avg(social_high_coherence) > _avg(social_low_coherence):
        findings.append("Speech coherence appeared stronger during periods with more social activity.")
        associations.append({"event": "social activity", "marker": "semantic coherence", "difference": round(_avg(social_high_coherence) - _avg(social_low_coherence), 2)})

    if not findings:
        findings.append("No strong event-to-voice association stands out yet, though the timeline can still help with context.")

    confidence = "high" if len(associations) >= 2 else "moderate" if associations else "low"
    return {
        "findings": findings,
        "strongest_associations": associations[:3],
        "confidence": confidence,
        "note": "These observations are described as associations only and may coincide with other day-to-day factors.",
    }

