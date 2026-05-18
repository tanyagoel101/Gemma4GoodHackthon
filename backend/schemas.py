from __future__ import annotations

import json
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PatientCreate(BaseModel):
    name: str
    age: int = Field(ge=1, le=120)
    location: str
    caregiver_name: str
    caregiver_relationship: str


class PatientRead(PatientCreate):
    id: str
    created_at: datetime
    total_sessions: int | None = None

    model_config = ConfigDict(from_attributes=True)


class SessionScores(BaseModel):
    ttr_score: float
    mlu_score: float
    filler_density: float
    idea_density: float
    referential_cohesion: float
    semantic_coherence: float
    composite_risk_score: float


class AcousticMarkers(BaseModel):
    words_per_minute: float = 0.0
    average_pause_duration: float = 0.0
    pause_frequency: float = 0.0
    speech_tempo_variability: float = 0.0
    vocal_energy: float = 0.0
    pitch_variability: float = 0.0
    jitter: float = 0.0
    shimmer: float = 0.0


class SessionInsights(BaseModel):
    caregiver_summary: str = ""
    clinician_summary: str = ""
    notable_changes: list[str] = Field(default_factory=list)
    stable_markers: list[str] = Field(default_factory=list)
    actionable_observations: list[str] = Field(default_factory=list)
    severity: Literal["low", "moderate", "high"] = "low"
    confidence: Literal["low", "moderate", "high"] = "low"
    trend_direction: Literal["improving", "stable", "declining"] = "stable"
    baseline_deviation: dict[str, float] = Field(default_factory=dict)
    alerts: list[str] = Field(default_factory=list)


class SessionRead(SessionScores):
    id: str
    patient_id: str
    recorded_at: datetime
    audio_filename: str
    transcript: str
    duration_seconds: float
    gemma_summary: str
    clinical_notes: str
    caregiver_insight: str = ""
    clinician_insight: str = ""
    confidence_level: str = "low"
    trend_direction: str = "stable"
    baseline_deviation_json: str = "{}"
    marker_evidence_json: str = "{}"
    prompt_text: str = ""
    prompt_category: str = "freeform"
    words_per_minute: float = 0.0
    average_pause_duration: float = 0.0
    pause_frequency: float = 0.0
    speech_tempo_variability: float = 0.0
    vocal_energy: float = 0.0
    pitch_variability: float = 0.0
    jitter: float = 0.0
    shimmer: float = 0.0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @property
    def baseline_deviation(self) -> dict[str, float]:
        try:
            return json.loads(self.baseline_deviation_json or "{}")
        except json.JSONDecodeError:
            return {}

    @property
    def marker_evidence(self) -> dict:
        try:
            return json.loads(self.marker_evidence_json or "{}")
        except json.JSONDecodeError:
            return {}


class RecordingUploadResponse(SessionRead):
    pass


class BaselineResponse(BaseModel):
    patient_id: str
    session_count: int
    baseline_start: datetime | None
    baseline_end: datetime | None
    markers: SessionScores
    acoustic_markers: AcousticMarkers = Field(default_factory=AcousticMarkers)


class LifeEventCreate(BaseModel):
    event_date: date
    sleep_quality: int = Field(ge=1, le=5, default=3)
    stress_level: int = Field(ge=1, le=5, default=3)
    illness: bool = False
    medication_change: bool = False
    missed_meals: bool = False
    social_activity: int = Field(ge=1, le=5, default=3)
    doctor_visit: bool = False
    freeform_notes: str = ""


class LifeEventRead(LifeEventCreate):
    id: str
    patient_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CorrelationResponse(BaseModel):
    patient_id: str
    findings: list[str]
    strongest_associations: list[dict[str, str | float]]
    confidence: Literal["low", "moderate", "high"]
    note: str


class DailyPromptResponse(BaseModel):
    prompt_text: str
    prompt_category: str
    targeted_domains: list[str]
    available_categories: list[str]


class WeeklySummaryResponse(BaseModel):
    id: str
    patient_id: str
    week_start: date
    summary_text: str
    avg_composite: float
    trend_direction: Literal["improving", "stable", "declining"]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClinicianPatientRow(BaseModel):
    id: str
    name: str
    age: int
    location: str
    caregiver_name: str
    caregiver_relationship: str
    latest_composite_risk_score: float | None
    trend_direction: Literal["improving", "stable", "declining"]
    confidence_level: Literal["low", "moderate", "high"] = "low"
    days_since_last_entry: int | None
    total_sessions: int
    last_entry_at: datetime | None
    clinician_summary: str = ""


class BriefResponse(BaseModel):
    patient_id: str
    patient_name: str
    generated_at: datetime
    content: str


class ReferralResponse(BaseModel):
    patient_id: str
    patient_name: str
    generated_at: datetime
    referring_gp: str
    content: str


class HealthStatus(BaseModel):
    status: Literal["ok", "degraded"]
    database: str
    ollama: str
    model: str
    message: str
