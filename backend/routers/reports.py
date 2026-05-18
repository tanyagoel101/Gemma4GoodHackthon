from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import LifeEvent, Patient, Session, WeeklySummary, get_db
from backend.services.pdf_generator import generate_patient_report_pdf
from backend.services.correlations import generate_correlations


router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{patient_id}/pdf")
async def download_patient_report(patient_id: str, db: AsyncSession = Depends(get_db)) -> Response:
    patient_result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = patient_result.scalar_one_or_none()
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found.")

    sessions_result = await db.execute(
        select(Session).where(Session.patient_id == patient_id).order_by(Session.recorded_at.desc())
    )
    sessions = sessions_result.scalars().all()
    if not sessions:
        raise HTTPException(status_code=404, detail="No sessions found for this patient.")

    summary_result = await db.execute(
        select(WeeklySummary).where(WeeklySummary.patient_id == patient_id).order_by(WeeklySummary.created_at.desc())
    )
    summary = summary_result.scalar_one_or_none()
    weekly_summary = summary.summary_text if summary else sessions[0].gemma_summary
    events_result = await db.execute(select(LifeEvent).where(LifeEvent.patient_id == patient_id).order_by(LifeEvent.event_date.desc()))
    correlation_data = generate_correlations(events_result.scalars().all(), sessions)
    pdf_bytes = generate_patient_report_pdf(patient, sessions, weekly_summary, correlation_data["findings"])
    filename = f"voicetrace-{patient.name.lower().replace(' ', '-')}-report.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
