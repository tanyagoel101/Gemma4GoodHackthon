from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import Patient, Session, get_db
from backend.schemas import DailyPromptResponse
from backend.services.prompts import generate_daily_prompt


router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.get("/daily/{patient_id}", response_model=DailyPromptResponse)
async def get_daily_prompt(
    patient_id: str,
    category: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> DailyPromptResponse:
    patient_result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = patient_result.scalar_one_or_none()
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found.")

    history_result = await db.execute(
        select(Session).where(Session.patient_id == patient_id).order_by(Session.recorded_at.desc()).limit(10)
    )
    prompt = generate_daily_prompt(history_result.scalars().all(), category_override=category, patient_name=patient.name)
    return DailyPromptResponse(**prompt)
