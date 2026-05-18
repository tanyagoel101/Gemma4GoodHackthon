from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import Patient, Session, get_db
from backend.schemas import BriefResponse, ClinicianPatientRow, ReferralResponse
from backend.services.gemma import (
    build_session_payloads,
    generate_preappointment_brief,
    generate_referral_letter,
)
from backend.utils import average_scores, calculate_trend_direction, days_since


router = APIRouter(prefix="/clinician", tags=["clinician"])


@router.get("/patients", response_model=list[ClinicianPatientRow])
async def list_clinician_patients(db: AsyncSession = Depends(get_db)) -> list[ClinicianPatientRow]:
    result = await db.execute(select(Patient).order_by(Patient.created_at.asc()))
    patients = result.scalars().all()
    rows: list[ClinicianPatientRow] = []
    for patient in patients:
        sessions_result = await db.execute(
            select(Session).where(Session.patient_id == patient.id).order_by(Session.recorded_at.desc())
        )
        sessions = sessions_result.scalars().all()
        latest = sessions[0] if sessions else None
        now = datetime.utcnow()
        current_window = [s for s in sessions if s.recorded_at >= now - timedelta(days=7)]
        previous_window = [
            s for s in sessions if now - timedelta(days=14) <= s.recorded_at < now - timedelta(days=7)
        ]
        current_avg = average_scores(current_window)["composite_risk_score"] if current_window else None
        previous_avg = average_scores(previous_window)["composite_risk_score"] if previous_window else None
        rows.append(
            ClinicianPatientRow(
                id=patient.id,
                name=patient.name,
                age=patient.age,
                location=patient.location,
                caregiver_name=patient.caregiver_name,
                caregiver_relationship=patient.caregiver_relationship,
                latest_composite_risk_score=latest.composite_risk_score if latest else None,
                trend_direction=calculate_trend_direction(current_avg, previous_avg),
                confidence_level=latest.confidence_level if latest else "low",
                days_since_last_entry=days_since(latest.recorded_at if latest else None),
                total_sessions=len(sessions),
                last_entry_at=latest.recorded_at if latest else None,
                clinician_summary=latest.clinician_insight if latest else "",
            )
        )
    return rows


async def _load_patient_with_sessions(patient_id: str, db: AsyncSession) -> tuple[Patient, list[Session]]:
    patient_result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = patient_result.scalar_one_or_none()
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found.")

    sessions_result = await db.execute(
        select(Session)
        .where(Session.patient_id == patient_id)
        .order_by(Session.recorded_at.desc())
    )
    sessions = sessions_result.scalars().all()
    if not sessions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No sessions found for this patient.")
    return patient, sessions


@router.get("/patients/{patient_id}/brief", response_model=BriefResponse)
async def get_preappointment_brief(patient_id: str, db: AsyncSession = Depends(get_db)) -> BriefResponse:
    patient, sessions = await _load_patient_with_sessions(patient_id, db)
    window = datetime.utcnow() - timedelta(days=30)
    recent_sessions = [session for session in sessions if session.recorded_at >= window]
    brief = await generate_preappointment_brief(build_session_payloads(recent_sessions or sessions), patient.__dict__)
    return BriefResponse(
        patient_id=patient.id,
        patient_name=patient.name,
        generated_at=datetime.utcnow(),
        content=brief,
    )


@router.get("/patients/{patient_id}/referral", response_model=ReferralResponse)
async def get_referral_letter(
    patient_id: str,
    referring_gp: str = Query(..., min_length=2),
    db: AsyncSession = Depends(get_db),
) -> ReferralResponse:
    patient, sessions = await _load_patient_with_sessions(patient_id, db)
    letter = await generate_referral_letter(patient.__dict__, build_session_payloads(sessions), referring_gp)
    return ReferralResponse(
        patient_id=patient.id,
        patient_name=patient.name,
        generated_at=datetime.utcnow(),
        referring_gp=referring_gp,
        content=letter,
    )
