from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import delete, select

from backend.database import AsyncSessionLocal, LifeEvent, Patient, Session, WeeklySummary, init_db
from backend.services.insights import generate_session_insights
from backend.services.prompts import generate_daily_prompt
from backend.services.transcript_evidence import build_marker_evidence, serialize_marker_evidence
from backend.services.trends import serialize_deviations, weighted_longitudinal_risk
from backend.utils import calculate_trend_direction, first_name


@dataclass
class Phase:
    ttr: float
    mlu: float
    filler: float
    idea: float
    cohesion: float
    coherence: float


def _vary(value: float, spread: float = 0.1, lower: float | None = None, upper: float | None = None) -> float:
    varied = value * random.uniform(1 - spread, 1 + spread)
    if lower is not None:
        varied = max(lower, varied)
    if upper is not None:
        varied = min(upper, varied)
    return round(varied, 3)


def _compose_summary(name: str, ttr: float, coherence: float, filler: float) -> tuple[str, str]:
    summary = (
        f"{first_name(name)} used {'steady' if ttr > 0.5 else 'simpler'} word variety today, "
        f"with {'clear' if coherence > 7 else 'more effortful'} storytelling and "
        f"{'light' if filler < 6 else 'noticeable'} pauses."
    )
    notes = (
        f"Vocabulary diversity measured at {ttr:.2f} and semantic coherence at {coherence:.1f}. "
        f"Filler density was {filler:.1f} per 100 words. Trends should be interpreted longitudinally."
    )
    return summary, notes


def _make_transcript(name: str, phase_label: str) -> str:
    return (
        f"My name is {first_name(name)} and this is my voice diary for {phase_label}. "
        "I talked about breakfast, a phone call with family, the weather, and a short walk in town. "
        "I also mentioned chores at home and how the day felt overall."
    )


def _create_session(patient_id: str, name: str, recorded_at: datetime, phase: Phase, phase_label: str) -> Session:
    ttr = _vary(phase.ttr, lower=0.2, upper=0.8)
    mlu = _vary(phase.mlu, lower=5, upper=20)
    filler = _vary(phase.filler, lower=1, upper=14)
    idea = _vary(phase.idea, lower=0.15, upper=0.85)
    cohesion = _vary(phase.cohesion, lower=0.1, upper=0.9)
    coherence = _vary(phase.coherence, lower=3.5, upper=9.5)
    summary, notes = _compose_summary(name, ttr, coherence, filler)
    markers = {
        "ttr_score": ttr,
        "mlu_score": mlu,
        "filler_density": filler,
        "idea_density": idea,
        "referential_cohesion": cohesion,
        "semantic_coherence": coherence,
        "gemma_summary": summary,
        "clinical_notes": notes,
    }
    return Session(
        patient_id=patient_id,
        recorded_at=recorded_at,
        audio_filename=f"{patient_id}-{recorded_at:%Y%m%d}.webm",
        transcript=_make_transcript(name, phase_label),
        duration_seconds=random.uniform(55, 115),
        prompt_text="",
        prompt_category="freeform",
        words_per_minute=round(random.uniform(88, 124), 2),
        average_pause_duration=round(random.uniform(0.22, 0.6), 3),
        pause_frequency=round(random.uniform(4.2, 9.4), 2),
        speech_tempo_variability=round(random.uniform(0.02, 0.08), 4),
        vocal_energy=round(random.uniform(0.02, 0.09), 4),
        pitch_variability=round(random.uniform(20, 55), 3),
        jitter=round(random.uniform(0.001, 0.01), 5),
        shimmer=round(random.uniform(0.01, 0.08), 5),
        composite_risk_score=0.0,
        caregiver_insight="",
        clinician_insight="",
        confidence_level="low",
        trend_direction="stable",
        baseline_deviation_json="{}",
        **markers,
    )


async def seed_demo_data() -> None:
    await init_db()
    async with AsyncSessionLocal() as db:
        for model in (WeeklySummary, LifeEvent, Session, Patient):
            await db.execute(delete(model))
        await db.commit()

        start = datetime.utcnow() - timedelta(weeks=8)
        patients = [
            Patient(
                name="Margaret Chen",
                age=74,
                location="rural Iowa",
                caregiver_name="David Chen",
                caregiver_relationship="son",
                created_at=start,
            ),
            Patient(
                name="Robert Okafor",
                age=71,
                location="rural Mississippi",
                caregiver_name="Amara Okafor",
                caregiver_relationship="daughter",
                created_at=datetime.utcnow() - timedelta(weeks=4),
            ),
            Patient(
                name="Eleanor Vasquez",
                age=68,
                location="rural New Mexico",
                caregiver_name="Maria Vasquez",
                caregiver_relationship="wife",
                created_at=datetime.utcnow() - timedelta(weeks=2),
            ),
        ]
        db.add_all(patients)
        await db.flush()

        margaret_phases = [
            Phase(0.58, 14.2, 4.1, 0.61, 0.29, 7.8),
            Phase(0.52, 12.8, 5.3, 0.54, 0.35, 7.2),
            Phase(0.45, 11.1, 6.8, 0.44, 0.48, 6.5),
            Phase(0.38, 9.4, 8.9, 0.31, 0.63, 5.7),
        ]
        robert_phases = [Phase(0.56, 13.8, 4.3, 0.58, 0.31, 7.6), Phase(0.59, 14.4, 3.8, 0.61, 0.28, 8.0)]
        eleanor_phase = Phase(0.55, 13.4, 4.6, 0.57, 0.33, 7.5)

        sessions: list[Session] = []
        current = start
        margaret_count = 0
        while margaret_count < 56:
            phase = margaret_phases[min(margaret_count // 14, 3)]
            sessions.append(_create_session(patients[0].id, patients[0].name, current, phase, f"week {margaret_count // 7 + 1}"))
            margaret_count += 1
            current += timedelta(days=1)

        current = datetime.utcnow() - timedelta(weeks=4)
        robert_count = 0
        while robert_count < 28:
            phase = robert_phases[min(robert_count // 14, 1)]
            sessions.append(_create_session(patients[1].id, patients[1].name, current, phase, f"week {robert_count // 7 + 1}"))
            robert_count += 1
            current += timedelta(days=1)

        current = datetime.utcnow() - timedelta(weeks=2)
        eleanor_count = 0
        while eleanor_count < 14:
            sessions.append(_create_session(patients[2].id, patients[2].name, current, eleanor_phase, f"week {eleanor_count // 7 + 1}"))
            eleanor_count += 1
            current += timedelta(days=1)

        db.add_all(sessions)
        await db.flush()

        for patient in patients:
            patient_sessions = [session for session in sessions if session.patient_id == patient.id]
            patient_sessions.sort(key=lambda session: session.recorded_at)
            for index, session in enumerate(patient_sessions):
                history = list(reversed(patient_sessions[:index]))
                baseline_source = patient_sessions[: min(14, len(patient_sessions[: index + 1]))]
                baseline_proxy = type(
                    "BaselineProxy",
                    (),
                    {
                        "ttr_score": sum(item.ttr_score for item in baseline_source) / len(baseline_source),
                        "mlu_score": sum(item.mlu_score for item in baseline_source) / len(baseline_source),
                        "filler_density": sum(item.filler_density for item in baseline_source) / len(baseline_source),
                        "idea_density": sum(item.idea_density for item in baseline_source) / len(baseline_source),
                        "referential_cohesion": sum(item.referential_cohesion for item in baseline_source) / len(baseline_source),
                        "semantic_coherence": sum(item.semantic_coherence for item in baseline_source) / len(baseline_source),
                        "words_per_minute": sum(item.words_per_minute for item in baseline_source) / len(baseline_source),
                        "average_pause_duration": sum(item.average_pause_duration for item in baseline_source) / len(baseline_source),
                        "pause_frequency": sum(item.pause_frequency for item in baseline_source) / len(baseline_source),
                        "speech_tempo_variability": sum(item.speech_tempo_variability for item in baseline_source) / len(baseline_source),
                        "vocal_energy": sum(item.vocal_energy for item in baseline_source) / len(baseline_source),
                        "pitch_variability": sum(item.pitch_variability for item in baseline_source) / len(baseline_source),
                        "jitter": sum(item.jitter for item in baseline_source) / len(baseline_source),
                        "shimmer": sum(item.shimmer for item in baseline_source) / len(baseline_source),
                    },
                )()
                prompt = generate_daily_prompt(list(reversed(patient_sessions[:index])), patient_name=patient.name)
                session.prompt_text = prompt["prompt_text"]
                session.prompt_category = prompt["prompt_category"]
                insights = generate_session_insights(session, baseline_proxy, history[:7])
                session.caregiver_insight = insights["caregiver_summary"]
                session.clinician_insight = insights["clinician_summary"]
                session.confidence_level = insights["confidence"]
                session.trend_direction = insights["trend_direction"]
                session.baseline_deviation_json = serialize_deviations(insights["baseline_deviation"])
                session.marker_evidence_json = serialize_marker_evidence(
                    build_marker_evidence(
                        session.transcript,
                        {
                            "ttr_score": session.ttr_score,
                            "mlu_score": session.mlu_score,
                            "filler_density": session.filler_density,
                            "idea_density": session.idea_density,
                            "referential_cohesion": session.referential_cohesion,
                            "semantic_coherence": session.semantic_coherence,
                        },
                        {
                            "words_per_minute": session.words_per_minute,
                            "average_pause_duration": session.average_pause_duration,
                            "pause_frequency": session.pause_frequency,
                            "pitch_variability": session.pitch_variability,
                            "vocal_energy": session.vocal_energy,
                            "duration_seconds": session.duration_seconds,
                        },
                    )
                )
                session.composite_risk_score = weighted_longitudinal_risk(session, history[:7], baseline_proxy, insights["baseline_deviation"])

        for patient in patients:
            patient_sessions = [session for session in sessions if session.patient_id == patient.id]
            patient_sessions.sort(key=lambda session: session.recorded_at)
            latest_week = patient_sessions[-7:]
            prior_week = patient_sessions[-14:-7]
            summary = WeeklySummary(
                patient_id=patient.id,
                week_start=latest_week[0].recorded_at.date(),
                summary_text=(
                    f"{first_name(patient.name)} showed "
                    f"{'more variation later in the week' if patient.name == 'Margaret Chen' else 'steady communication patterns across the week'}, "
                    "with day-to-day changes that are easier to interpret against the personal baseline."
                ),
                avg_composite=round(sum(item.composite_risk_score for item in latest_week) / len(latest_week), 2),
                trend_direction=calculate_trend_direction(
                    sum(item.composite_risk_score for item in latest_week) / len(latest_week),
                    (sum(item.composite_risk_score for item in prior_week) / len(prior_week)) if prior_week else None,
                ),
            )
            db.add(summary)

        sample_events = [
            LifeEvent(
                patient_id=patients[0].id,
                event_date=(datetime.utcnow() - timedelta(days=10)).date(),
                sleep_quality=2,
                stress_level=4,
                medication_change=True,
                social_activity=2,
                freeform_notes="Slept poorly and felt more rushed this week.",
            ),
            LifeEvent(
                patient_id=patients[0].id,
                event_date=(datetime.utcnow() - timedelta(days=3)).date(),
                sleep_quality=4,
                stress_level=2,
                social_activity=4,
                freeform_notes="Spent time with family and felt more settled.",
            ),
            LifeEvent(
                patient_id=patients[1].id,
                event_date=(datetime.utcnow() - timedelta(days=6)).date(),
                sleep_quality=4,
                stress_level=2,
                social_activity=5,
                doctor_visit=True,
                freeform_notes="Routine check-in and a busy social weekend.",
            ),
        ]
        db.add_all(sample_events)

        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed_demo_data())
