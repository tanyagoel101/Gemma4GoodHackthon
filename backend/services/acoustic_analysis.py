from __future__ import annotations

from pathlib import Path

try:
    import librosa
    import numpy as np
    import parselmouth
except Exception:  # noqa: BLE001
    librosa = None
    np = None
    parselmouth = None


def extract_acoustic_markers(audio_path: str, transcript: str = "") -> dict[str, float]:
    if not librosa or not np:
        return _empty_acoustic_markers()

    try:
        signal, sample_rate = librosa.load(audio_path, sr=None, mono=True)
        duration_seconds = max(librosa.get_duration(y=signal, sr=sample_rate), 1e-6)
        rms = librosa.feature.rms(y=signal)[0]
        pitches, magnitudes = librosa.piptrack(y=signal, sr=sample_rate)
        pitch_values = pitches[magnitudes > np.median(magnitudes[magnitudes > 0])] if np.any(magnitudes > 0) else np.array([])

        intervals = librosa.effects.split(signal, top_db=25)
        if len(intervals) > 1:
            pauses = []
            previous_end = intervals[0][1]
            for start, end in intervals[1:]:
                pause_duration = max(0.0, (start - previous_end) / sample_rate)
                if pause_duration > 0.08:
                    pauses.append(pause_duration)
                previous_end = end
        else:
            pauses = []

        words = len(transcript.split()) if transcript else 0
        voice_metrics = _praat_voice_metrics(audio_path)
        return {
            "words_per_minute": round((words / duration_seconds) * 60, 2) if words else 0.0,
            "average_pause_duration": round(float(np.mean(pauses)) if pauses else 0.0, 3),
            "pause_frequency": round((len(pauses) / duration_seconds) * 60, 2),
            "speech_tempo_variability": round(float(np.std(librosa.feature.zero_crossing_rate(y=signal)[0])), 4),
            "vocal_energy": round(float(np.mean(rms)), 4),
            "pitch_variability": round(float(np.std(pitch_values)) if pitch_values.size else 0.0, 3),
            "jitter": voice_metrics["jitter"],
            "shimmer": voice_metrics["shimmer"],
        }
    except Exception:  # noqa: BLE001
        return _empty_acoustic_markers()


def _praat_voice_metrics(audio_path: str) -> dict[str, float]:
    if not parselmouth:
        return {"jitter": 0.0, "shimmer": 0.0}
    try:
        sound = parselmouth.Sound(audio_path)
        point_process = parselmouth.praat.call(sound, "To PointProcess (periodic, cc)", 75, 500)
        jitter = parselmouth.praat.call(point_process, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
        shimmer = parselmouth.praat.call([sound, point_process], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
        return {"jitter": round(float(jitter or 0.0), 5), "shimmer": round(float(shimmer or 0.0), 5)}
    except Exception:  # noqa: BLE001
        return {"jitter": 0.0, "shimmer": 0.0}


def _empty_acoustic_markers() -> dict[str, float]:
    return {
        "words_per_minute": 0.0,
        "average_pause_duration": 0.0,
        "pause_frequency": 0.0,
        "speech_tempo_variability": 0.0,
        "vocal_energy": 0.0,
        "pitch_variability": 0.0,
        "jitter": 0.0,
        "shimmer": 0.0,
    }
