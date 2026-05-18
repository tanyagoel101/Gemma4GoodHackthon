from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import BinaryIO

from faster_whisper import WhisperModel
from fastapi import HTTPException, UploadFile, status

from backend.config import get_settings


settings = get_settings()
ALLOWED_EXTENSIONS = {".webm", ".mp4", ".wav", ".ogg"}

_whisper_model: WhisperModel | None = None


def _get_whisper_model() -> WhisperModel:
    global _whisper_model
    if _whisper_model is None:
        _whisper_model = WhisperModel(settings.whisper_model, device="auto", compute_type="int8")
    return _whisper_model


def validate_audio_upload(upload: UploadFile) -> str:
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported audio type. Accepted formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}.",
        )
    return suffix


def _transcribe_file_sync(temp_path: str) -> tuple[str, float]:
    model = _get_whisper_model()
    segments, info = model.transcribe(temp_path, beam_size=5, vad_filter=True)
    transcript_parts = [segment.text.strip() for segment in segments if segment.text.strip()]
    transcript = " ".join(transcript_parts).strip()
    duration = float(info.duration or 0.0)
    if duration > settings.max_audio_minutes * 60:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Audio exceeds {settings.max_audio_minutes} minute limit.",
        )
    return transcript, duration


async def _transcribe_bytes_to_temp(data: bytes, suffix: str) -> tuple[str, float]:
    settings.upload_dir.mkdir(parents=True, exist_ok=True)

    with NamedTemporaryFile(delete=False, dir=settings.upload_dir, suffix=suffix) as tmp:
        temp_path = tmp.name
        tmp.write(data)
        tmp.flush()

    try:
        return await asyncio.to_thread(_transcribe_file_sync, temp_path)
    finally:
        Path(temp_path).unlink(missing_ok=True)


async def transcribe_upload(upload: UploadFile) -> tuple[str, float]:
    suffix = validate_audio_upload(upload)
    data = upload.file.read()
    try:
        return await _transcribe_bytes_to_temp(data, suffix)
    finally:
        await upload.close()


async def transcribe_bytes(data: bytes, filename: str) -> tuple[str, float]:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported audio type. Accepted formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}.",
        )
    return await _transcribe_bytes_to_temp(data, suffix)


async def _copy_upload(source: BinaryIO, target) -> None:
    while chunk := source.read(1024 * 1024):
        target.write(chunk)
    target.flush()
