from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import Session, get_db


router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("")
async def list_sessions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Session).order_by(Session.recorded_at.desc()))
    return result.scalars().all()

