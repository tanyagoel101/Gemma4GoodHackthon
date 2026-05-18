# VoiceTrace

VoiceTrace is a local-first cognitive health monitoring application designed to help families and rural clinicians notice meaningful speech-pattern changes earlier, even where specialist access is limited. It combines caregiver voice diaries, longitudinal neurolinguistic trend tracking, and clinician-ready summaries powered by Gemma 4 through Ollama, while keeping all audio and transcript data on the device.

## Prerequisites

- Python 3.11+
- Node.js 18+
- Ollama installed locally

## Setup

1. Pull the local Gemma model:

```bash
ollama pull gemma4
```

Fallback if needed:

```bash
ollama pull gemma3:27b
```

2. Install backend dependencies:

```bash
pip install -r requirements.txt
```

3. Seed demo data:

```bash
python -m backend.seed_data
```

4. Start the backend:

```bash
uvicorn backend.main:app --reload
```

5. Start the frontend:

```bash
cd frontend
npm install
npm run dev
```

## Architecture

```text
┌──────────────────────────────┐
│          React SPA           │
│ Caregiver + Clinician Views  │
└──────────────┬───────────────┘
               │ REST / Axios
┌──────────────▼───────────────┐
│        FastAPI Backend       │
│ Routers + async services     │
└───────┬───────────┬──────────┘
        │           │
        │           ├───────────────┐
        │                           │
┌───────▼────────┐        ┌─────────▼─────────┐
│  SQLite DB     │        │ Ollama + Gemma 4  │
│ patients/sessions│      │ local LLM analysis│
└────────────────┘        └───────────────────┘
        │
┌───────▼────────┐
│ faster-whisper │
│ transcription  │
└────────────────┘
```

## Six Linguistic Markers

1. `ttr_score`: How much vocabulary variety appears in a diary entry. Lower variety over time can suggest language narrowing.
2. `mlu_score`: The average number of words per sentence. Shorter, simpler sentences can be worth tracking longitudinally.
3. `filler_density`: How often filler phrases like “um” or “you know” appear per 100 words. Rising filler use can reflect more effortful speech.
4. `idea_density`: How much information is packed into the speech. Lower idea density can mean fewer concrete details or facts.
5. `referential_cohesion`: How often vague pronouns appear relative to named things. A higher ratio can signal increasing reliance on vague references.
6. `semantic_coherence`: How well the narrative stays on topic and reaches a clear point. Lower coherence can show more fragmented storytelling.

## Development Notes

- The `/health` endpoint verifies database access, Ollama reachability, and whether `gemma4` is installed.
- Audio uploads are stored only temporarily for transcription and then deleted.
- Clinician-facing screens include a visible non-diagnostic disclaimer.
- The frontend blocks new AI analysis actions when Ollama or `gemma4` is unavailable and shows setup guidance instead.

## Links

- Live Demo: _TBD_
- Video: _TBD_
- Kaggle Writeup: _TBD_

## Disclaimer

VoiceTrace is for clinical support only. It is not a diagnostic tool, does not replace clinical judgment, and all AI-generated briefs or referral text require physician review before use.

## Credits And Research

- DementiaBank corpus
- Snowdon et al. nun study on idea density
- Iris Murdoch linguistic analysis studies
- HRSA reporting on rural specialist shortages
