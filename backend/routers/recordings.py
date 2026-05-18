from __future__ import annotations

import logging
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import Patient, Session, get_db
from backend.schemas import RecordingUploadResponse
from backend.services.acoustic_analysis import extract_acoustic_markers
from backend.services.gemma import extract_linguistic_markers
from backend.services.insights import generate_session_insights
from backend.services.transcript_evidence import build_marker_evidence, serialize_marker_evidence
from backend.services.transcription import transcribe_bytes, transcribe_upload
from backend.services.trends import serialize_deviations, weighted_longitudinal_risk
from backend.utils import build_baseline_scores


router = APIRouter(prefix="/recordings", tags=["recordings"])
logger = logging.getLogger("uvicorn.error")


async def _save_session(
    *,
    db: AsyncSession,
    patient: Patient,
    patient_id: str,
    filename: str,
    audio_bytes: bytes,
    transcript: str,
    duration_seconds: float,
    prompt_text: str = "",
    prompt_category: str = "freeform",
):
    logger.info("Starting Gemma analysis for patient_id=%s", patient_id)
    markers = await extract_linguistic_markers(transcript)
    logger.info("Gemma analysis complete for patient_id=%s composite_risk_score=%.2f", patient_id, markers["composite_risk_score"])
    temp_audio_path = None
    try:
        suffix = Path(filename).suffix or ".webm"
        temp_audio_path = f"{filename}{suffix}" if not filename.endswith(suffix) else filename
        tmp_file = Path("/tmp") / f"voicetrace-{patient_id}{suffix}"
        tmp_file.write_bytes(audio_bytes)
        acoustic_markers = extract_acoustic_markers(str(tmp_file), transcript)
    except Exception:  # noqa: BLE001
        acoustic_markers = extract_acoustic_markers("", transcript)
    finally:
        if temp_audio_path:
            tmp_candidate = Path("/tmp") / f"voicetrace-{patient_id}{Path(filename).suffix or '.webm'}"
            tmp_candidate.unlink(missing_ok=True)

    history_result = await db.execute(
        select(Session).where(Session.patient_id == patient_id).order_by(Session.recorded_at.desc())
    )
    history = history_result.scalars().all()
    baseline_sessions = list(reversed(history))[:14] if history else []
    baseline_markers = build_baseline_scores(baseline_sessions)
    provisional_session = type("ProvisionalSession", (), {**markers, **acoustic_markers})()
    insights = generate_session_insights(provisional_session, baseline_markers, history[:7])
    evidence_acoustic_markers = {
        **acoustic_markers,
        "duration_seconds": duration_seconds,
    }
    marker_evidence = build_marker_evidence(
        transcript,
        markers,
        evidence_acoustic_markers,
    )
    markers["composite_risk_score"] = weighted_longitudinal_risk(
        provisional_session,
        history[:7],
        baseline_markers,
        insights["baseline_deviation"],
    )
    session = Session(
        patient_id=patient_id,
        recorded_at=datetime.utcnow(),
        audio_filename=filename or "recording.webm",
        transcript=transcript,
        duration_seconds=duration_seconds,
        caregiver_insight=insights["caregiver_summary"],
        clinician_insight=insights["clinician_summary"],
        confidence_level=insights["confidence"],
        trend_direction=insights["trend_direction"],
        baseline_deviation_json=serialize_deviations(insights["baseline_deviation"]),
        marker_evidence_json=serialize_marker_evidence(marker_evidence),
        prompt_text=prompt_text,
        prompt_category=prompt_category,
        **acoustic_markers,
        **markers,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    logger.info("Session saved for patient_id=%s session_id=%s", patient_id, session.id)
    return {
        "id": session.id,
        "patient_id": session.patient_id,
        "recorded_at": session.recorded_at,
        "audio_filename": session.audio_filename,
        "transcript": session.transcript,
        "duration_seconds": session.duration_seconds,
        "ttr_score": session.ttr_score,
        "mlu_score": session.mlu_score,
        "filler_density": session.filler_density,
        "idea_density": session.idea_density,
        "referential_cohesion": session.referential_cohesion,
        "semantic_coherence": session.semantic_coherence,
        "composite_risk_score": session.composite_risk_score,
        "gemma_summary": session.gemma_summary,
        "clinical_notes": session.clinical_notes,
        "caregiver_insight": session.caregiver_insight,
        "clinician_insight": session.clinician_insight,
        "confidence_level": session.confidence_level,
        "trend_direction": session.trend_direction,
        "baseline_deviation_json": session.baseline_deviation_json,
        "marker_evidence_json": session.marker_evidence_json,
        "prompt_text": session.prompt_text,
        "prompt_category": session.prompt_category,
        "words_per_minute": session.words_per_minute,
        "average_pause_duration": session.average_pause_duration,
        "pause_frequency": session.pause_frequency,
        "speech_tempo_variability": session.speech_tempo_variability,
        "vocal_energy": session.vocal_energy,
        "pitch_variability": session.pitch_variability,
        "jitter": session.jitter,
        "shimmer": session.shimmer,
        "created_at": session.created_at,
    }


@router.post("/upload", response_model=RecordingUploadResponse)
async def upload_recording(
    patient_id: str = Form(...),
    audio: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    logger.info("Recording upload received for patient_id=%s filename=%s", patient_id, audio.filename)
    patient_result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = patient_result.scalar_one_or_none()
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found.")

    logger.info("Starting transcription for patient_id=%s", patient_id)
    raw_bytes = audio.file.read()
    audio.file.seek(0)
    transcript, duration_seconds = await transcribe_upload(audio)
    if not transcript:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No speech detected in the upload.")

    logger.info("Transcription complete for patient_id=%s duration_seconds=%.2f", patient_id, duration_seconds)
    return await _save_session(
        db=db,
        patient=patient,
        patient_id=patient_id,
        filename=audio.filename or "recording.webm",
        audio_bytes=raw_bytes,
        transcript=transcript,
        duration_seconds=duration_seconds,
    )


@router.post("/upload-blob", response_model=RecordingUploadResponse)
async def upload_recording_blob(
    patient_id: str = Query(...),
    filename: str = Query("recording.webm"),
    prompt_text: str = Query(""),
    prompt_category: str = Query("freeform"),
    audio: bytes = Body(...),
    db: AsyncSession = Depends(get_db),
):
    logger.info("Raw blob upload received for patient_id=%s filename=%s bytes=%s", patient_id, filename, len(audio))
    patient_result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = patient_result.scalar_one_or_none()
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found.")

    logger.info("Starting transcription for raw blob patient_id=%s", patient_id)
    transcript, duration_seconds = await transcribe_bytes(audio, filename)
    if not transcript:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No speech detected in the upload.")

    logger.info("Transcription complete for raw blob patient_id=%s duration_seconds=%.2f", patient_id, duration_seconds)
    return await _save_session(
        db=db,
        patient=patient,
        patient_id=patient_id,
        filename=filename,
        audio_bytes=audio,
        transcript=transcript,
        duration_seconds=duration_seconds,
        prompt_text=prompt_text,
        prompt_category=prompt_category,
    )
