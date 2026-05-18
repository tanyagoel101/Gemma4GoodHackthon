from __future__ import annotations

from datetime import date, datetime
from typing import AsyncGenerator
from uuid import uuid4

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .config import get_settings


settings = get_settings()
engine = create_async_engine(settings.database_url, future=True, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    caregiver_name: Mapped[str] = mapped_column(String(255), nullable=False)
    caregiver_relationship: Mapped[str] = mapped_column(String(255), nullable=False)

    sessions: Mapped[list["Session"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan", order_by="desc(Session.recorded_at)"
    )
    weekly_summaries: Mapped[list["WeeklySummary"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    audio_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    transcript: Mapped[str] = mapped_column(Text, nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    ttr_score: Mapped[float] = mapped_column(Float, nullable=False)
    mlu_score: Mapped[float] = mapped_column(Float, nullable=False)
    filler_density: Mapped[float] = mapped_column(Float, nullable=False)
    idea_density: Mapped[float] = mapped_column(Float, nullable=False)
    referential_cohesion: Mapped[float] = mapped_column(Float, nullable=False)
    semantic_coherence: Mapped[float] = mapped_column(Float, nullable=False)
    composite_risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    gemma_summary: Mapped[str] = mapped_column(Text, nullable=False)
    clinical_notes: Mapped[str] = mapped_column(Text, nullable=False)
    caregiver_insight: Mapped[str] = mapped_column(Text, default="", nullable=False)
    clinician_insight: Mapped[str] = mapped_column(Text, default="", nullable=False)
    confidence_level: Mapped[str] = mapped_column(String(32), default="low", nullable=False)
    trend_direction: Mapped[str] = mapped_column(String(32), default="stable", nullable=False)
    baseline_deviation_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    marker_evidence_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    prompt_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    prompt_category: Mapped[str] = mapped_column(String(64), default="freeform", nullable=False)
    words_per_minute: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    average_pause_duration: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    pause_frequency: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    speech_tempo_variability: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    vocal_energy: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    pitch_variability: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    jitter: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    shimmer: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    patient: Mapped["Patient"] = relationship(back_populates="sessions")


class WeeklySummary(Base):
    __tablename__ = "weekly_summaries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    avg_composite: Mapped[float] = mapped_column(Float, nullable=False)
    trend_direction: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    patient: Mapped["Patient"] = relationship(back_populates="weekly_summaries")


class LifeEvent(Base):
    __tablename__ = "life_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    sleep_quality: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    stress_level: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    illness: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    medication_change: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    missed_meals: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    social_activity: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    doctor_visit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    freeform_notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

    patient: Mapped["Patient"] = relationship()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _migrate_schema(conn)


SESSION_MIGRATIONS = {
    "caregiver_insight": "TEXT NOT NULL DEFAULT ''",
    "clinician_insight": "TEXT NOT NULL DEFAULT ''",
    "confidence_level": "VARCHAR(32) NOT NULL DEFAULT 'low'",
    "trend_direction": "VARCHAR(32) NOT NULL DEFAULT 'stable'",
    "baseline_deviation_json": "TEXT NOT NULL DEFAULT '{}'",
    "marker_evidence_json": "TEXT NOT NULL DEFAULT '{}'",
    "prompt_text": "TEXT NOT NULL DEFAULT ''",
    "prompt_category": "VARCHAR(64) NOT NULL DEFAULT 'freeform'",
    "words_per_minute": "FLOAT NOT NULL DEFAULT 0",
    "average_pause_duration": "FLOAT NOT NULL DEFAULT 0",
    "pause_frequency": "FLOAT NOT NULL DEFAULT 0",
    "speech_tempo_variability": "FLOAT NOT NULL DEFAULT 0",
    "vocal_energy": "FLOAT NOT NULL DEFAULT 0",
    "pitch_variability": "FLOAT NOT NULL DEFAULT 0",
    "jitter": "FLOAT NOT NULL DEFAULT 0",
    "shimmer": "FLOAT NOT NULL DEFAULT 0",
}


async def _migrate_schema(conn) -> None:
    result = await conn.execute(text("PRAGMA table_info(sessions)"))
    existing_session_columns = {row[1] for row in result.fetchall()}
    for column_name, column_sql in SESSION_MIGRATIONS.items():
        if column_name not in existing_session_columns:
            await conn.execute(text(f"ALTER TABLE sessions ADD COLUMN {column_name} {column_sql}"))
