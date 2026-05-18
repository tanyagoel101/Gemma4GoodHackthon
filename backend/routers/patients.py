from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import LifeEvent, Patient, Session, WeeklySummary, get_db
from backend.schemas import (
    BaselineResponse,
    CorrelationResponse,
    LifeEventCreate,
    LifeEventRead,
    PatientCreate,
    PatientRead,
    SessionRead,
    WeeklySummaryResponse,
)
from backend.services.correlations import generate_correlations
from backend.services.gemma import build_session_payloads, generate_weekly_summary
from backend.utils import (
    average_scores,
    build_baseline_acoustics,
    build_baseline_scores,
    calculate_trend_direction,
)


router = APIRouter(prefix="/patients", tags=["patients"])


async def _get_patient_or_404(patient_id: str, db: AsyncSession) -> Patient:
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found.")
    return patient


@router.post("", response_model=PatientRead, status_code=status.HTTP_201_CREATED)
async def create_patient(payload: PatientCreate, db: AsyncSession = Depends(get_db)) -> Patient:
    patient = Patient(**payload.model_dump())
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    return patient


@router.get("", response_model=list[PatientRead])
async def list_patients(db: AsyncSession = Depends(get_db)) -> list[PatientRead]:
    result = await db.execute(
        select(Patient, func.count(Session.id).label("total_sessions"))
        .outerjoin(Session, Session.patient_id == Patient.id)
        .group_by(Patient.id)
        .order_by(Patient.created_at.asc())
    )
    rows = result.all()
    return [
        PatientRead.model_validate(
            {
                **patient.__dict__,
                "total_sessions": total_sessions,
            }
        )
        for patient, total_sessions in rows
    ]


@router.get("/{patient_id}/sessions", response_model=list[SessionRead])
async def get_patient_sessions(patient_id: str, db: AsyncSession = Depends(get_db)):
    await _get_patient_or_404(patient_id, db)
    result = await db.execute(
        select(Session).where(Session.patient_id == patient_id).order_by(Session.recorded_at.desc())
    )
    return result.scalars().all()


@router.get("/{patient_id}/baseline", response_model=BaselineResponse)
async def get_patient_baseline(patient_id: str, db: AsyncSession = Depends(get_db)) -> BaselineResponse:
    await _get_patient_or_404(patient_id, db)
    sessions_result = await db.execute(
        select(Session).where(Session.patient_id == patient_id).order_by(Session.recorded_at.asc())
    )
    sessions = sessions_result.scalars().all()
    if not sessions:
        return BaselineResponse(
            patient_id=patient_id,
            session_count=0,
            baseline_start=None,
            baseline_end=None,
            markers=build_baseline_scores([]),
            acoustic_markers=build_baseline_acoustics([]),
        )

    baseline_start = sessions[0].recorded_at
    cutoff = baseline_start + timedelta(days=14)
    baseline_sessions = [session for session in sessions if session.recorded_at <= cutoff]
    return BaselineResponse(
        patient_id=patient_id,
        session_count=len(baseline_sessions),
        baseline_start=baseline_sessions[0].recorded_at,
        baseline_end=baseline_sessions[-1].recorded_at,
        markers=build_baseline_scores(baseline_sessions),
        acoustic_markers=build_baseline_acoustics(baseline_sessions),
    )


@router.get("/{patient_id}/weekly-summary", response_model=WeeklySummaryResponse)
async def get_weekly_summary(patient_id: str, db: AsyncSession = Depends(get_db)) -> WeeklySummary:
    patient = await _get_patient_or_404(patient_id, db)
    today = datetime.utcnow().date()

    cached_result = await db.execute(
        select(WeeklySummary)
        .where(WeeklySummary.patient_id == patient_id, WeeklySummary.created_at >= datetime.combine(today, datetime.min.time()))
        .order_by(WeeklySummary.created_at.desc())
    )
    cached = cached_result.scalar_one_or_none()
    if cached is not None:
        return cached

    sessions_result = await db.execute(
        select(Session).where(Session.patient_id == patient_id).order_by(Session.recorded_at.desc()).limit(7)
    )
    sessions = sessions_result.scalars().all()
    if not sessions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No sessions found for this patient.")

    summary_text = await generate_weekly_summary(build_session_payloads(sessions), patient.name)
    score_values = average_scores(sessions)
    current_avg = score_values["composite_risk_score"]

    previous_result = await db.execute(
        select(Session)
        .where(Session.patient_id == patient_id, Session.recorded_at < sessions[-1].recorded_at)
        .order_by(Session.recorded_at.desc())
        .limit(7)
    )
    previous_sessions = previous_result.scalars().all()
    previous_avg = average_scores(previous_sessions)["composite_risk_score"] if previous_sessions else None

    summary = WeeklySummary(
        patient_id=patient_id,
        week_start=sessions[-1].recorded_at.date(),
        summary_text=summary_text,
        avg_composite=current_avg,
        trend_direction=calculate_trend_direction(current_avg, previous_avg),
    )
    db.add(summary)
    await db.commit()
    await db.refresh(summary)
    return summary


@router.post("/{patient_id}/events", response_model=LifeEventRead, status_code=status.HTTP_201_CREATED)
async def create_life_event(
    patient_id: str,
    payload: LifeEventCreate,
    db: AsyncSession = Depends(get_db),
) -> LifeEvent:
    await _get_patient_or_404(patient_id, db)
    event = LifeEvent(patient_id=patient_id, **payload.model_dump())
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


@router.get("/{patient_id}/events", response_model=list[LifeEventRead])
async def list_life_events(patient_id: str, db: AsyncSession = Depends(get_db)) -> list[LifeEvent]:
    await _get_patient_or_404(patient_id, db)
    result = await db.execute(
        select(LifeEvent).where(LifeEvent.patient_id == patient_id).order_by(LifeEvent.event_date.desc(), LifeEvent.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{patient_id}/correlations", response_model=CorrelationResponse)
async def get_correlations(patient_id: str, db: AsyncSession = Depends(get_db)) -> CorrelationResponse:
    await _get_patient_or_404(patient_id, db)
    events_result = await db.execute(
        select(LifeEvent).where(LifeEvent.patient_id == patient_id).order_by(LifeEvent.event_date.desc())
    )
    sessions_result = await db.execute(
        select(Session).where(Session.patient_id == patient_id).order_by(Session.recorded_at.desc())
    )
    results = generate_correlations(events_result.scalars().all(), sessions_result.scalars().all())
    return CorrelationResponse(patient_id=patient_id, **results)
