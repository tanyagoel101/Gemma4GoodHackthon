import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getDailyPrompt, getPatients, uploadRecording } from "../api/client";
import WaveformRecorder from "../components/WaveformRecorder";

const markerMeta = [
  ["ttr_score", "Vocabulary variety", 1],
  ["mlu_score", "Sentence length", 20],
  ["filler_density", "Filler density", 12],
  ["idea_density", "Idea density", 1],
  ["referential_cohesion", "Referential cohesion", 1],
  ["semantic_coherence", "Semantic coherence", 10],
];

const evidenceKeys = {
  ttr_score: "ttr_score",
  mlu_score: "mlu_score",
  filler_density: "filler_density",
  idea_density: "idea_density",
  referential_cohesion: "referential_cohesion",
  semantic_coherence: "semantic_coherence",
};

const loadingStages = [
  "Uploading your recording...",
  "Transcribing audio locally...",
  "Analyzing the transcript with Gemma 4...",
];

export default function RecordDiary({ health }) {
  const { patientId } = useParams();
  const [patient, setPatient] = useState(null);
  const [loading, setLoading] = useState(false);
  const [session, setSession] = useState(null);
  const [error, setError] = useState("");
  const [loadingStageIndex, setLoadingStageIndex] = useState(0);
  const [dailyPrompt, setDailyPrompt] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState("");
  const [promptMode, setPromptMode] = useState("guided");

  useEffect(() => {
    getPatients().then((rows) => setPatient(rows.find((entry) => entry.id === patientId) ?? null));
  }, [patientId]);

  useEffect(() => {
    getDailyPrompt(patientId).then((data) => {
      setDailyPrompt(data);
      setSelectedCategory(data.prompt_category);
    });
  }, [patientId]);

  useEffect(() => {
    if (!loading) return undefined;

    setLoadingStageIndex(0);
    const firstTimer = window.setTimeout(() => setLoadingStageIndex(1), 1500);
    const secondTimer = window.setTimeout(() => setLoadingStageIndex(2), 6000);

    return () => {
      window.clearTimeout(firstTimer);
      window.clearTimeout(secondTimer);
    };
  }, [loading]);

  const handleComplete = async (blob) => {
    setLoading(true);
    setError("");
    setSession(null);
    try {
      const data = await uploadRecording(patientId, blob, "recording.webm", {
        promptText: promptMode === "freeform" ? "" : dailyPrompt?.prompt_text ?? "",
        promptCategory: promptMode === "freeform" ? "freeform" : selectedCategory || dailyPrompt?.prompt_category || "freeform",
      });
      setSession(data);
    } catch (requestError) {
      setError(
        requestError?.code === "ECONNABORTED"
          ? "The local analysis took too long to respond. Please try a shorter recording first to warm up the models."
          : requestError?.response?.data?.detail ??
          "VoiceTrace could not finish the transcription and analysis for this recording. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  };

  const blocked = health?.status === "degraded";
  const markerEvidence = session?.marker_evidence_json ? JSON.parse(session.marker_evidence_json) : {};

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.2em] text-teal-700">Daily Diary</p>
          <h2 className="text-3xl font-semibold text-ink">Record a new entry for {patient?.name ?? "this patient"}</h2>
        </div>
        <Link className="rounded-full bg-white px-4 py-2 font-medium text-ink shadow-calm" to={`/patients/${patientId}/dashboard`}>
          View Dashboard
        </Link>
      </div>

      <WaveformRecorder disabled={blocked || loading} onComplete={handleComplete} />

      <section className="glass-card p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-sm uppercase tracking-[0.2em] text-teal-700">Today&apos;s Reflection Prompt</p>
            <h3 className="mt-2 text-2xl font-semibold text-ink">
              {promptMode === "freeform" ? "Freeform diary entry" : dailyPrompt?.prompt_text ?? "Loading today’s prompt..."}
            </h3>
            <p className="mt-3 text-slate-600">Take your time. There are no right or wrong answers.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button className="rounded-full bg-sky-100 px-4 py-2 text-sm font-medium text-ink" onClick={() => getDailyPrompt(patientId, selectedCategory || undefined).then(setDailyPrompt)} type="button">
              Regenerate prompt
            </button>
            <button className="rounded-full bg-white px-4 py-2 text-sm font-medium text-ink shadow-calm" onClick={() => setPromptMode((mode) => mode === "freeform" ? "guided" : "freeform")} type="button">
              {promptMode === "freeform" ? "Use guided prompt" : "Freeform mode"}
            </button>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <label className="text-sm font-medium text-slate-700">
            Prompt category
            <select className="ml-3 rounded-full border border-slate-200 px-4 py-2" onChange={(event) => {
              setSelectedCategory(event.target.value);
              getDailyPrompt(patientId, event.target.value).then(setDailyPrompt);
            }} value={selectedCategory}>
              {(dailyPrompt?.available_categories ?? []).map((category) => (
                <option key={category} value={category}>{category}</option>
              ))}
            </select>
          </label>
        </div>
      </section>

      {loading && (
        <section className="glass-card p-6">
          <p className="text-xl font-semibold text-ink">{loadingStages[loadingStageIndex]}</p>
          <p className="mt-2 text-slate-600">
            {loadingStageIndex === 0 && "VoiceTrace is sending the recording to the local backend now."}
            {loadingStageIndex === 1 &&
              "The speech recognizer is turning your audio into text on this device. The first run can take longer while the model warms up."}
            {loadingStageIndex === 2 &&
              "Gemma 4 is reviewing the transcript locally and extracting linguistic markers for this session."}
          </p>
        </section>
      )}

      {error && (
        <section className="glass-card border border-rose-200 bg-rose-50 p-6">
          <p className="text-lg font-semibold text-rose-900">Analysis could not complete</p>
          <p className="mt-2 text-rose-800">{error}</p>
        </section>
      )}

      {session && (
        <section className="glass-card p-6">
          <h3 className="text-2xl font-semibold text-ink">Today&apos;s Session Snapshot</h3>
          <p className="mt-3 rounded-3xl bg-skywash px-5 py-4 leading-8 text-slate-700">{session.gemma_summary}</p>
          <p className="mt-3 rounded-3xl bg-seafoam px-5 py-4 leading-8 text-slate-700">{session.caregiver_insight}</p>
          <div className="mt-6 grid gap-4 md:grid-cols-2">
            {markerMeta.map(([key, label, max]) => (
              <div key={key}>
                <div className="mb-2 flex items-center justify-between">
                  <span className="font-medium text-slate-700">{label}</span>
                  <span className="text-slate-500">{Number(session[key]).toFixed(2)}</span>
                </div>
                <div className="metric-bar">
                  <span style={{ width: `${Math.min(100, (Number(session[key]) / max) * 100)}%` }} />
                </div>
                {markerEvidence[evidenceKeys[key]] && (
                  <div className="mt-3 rounded-2xl bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-600">
                    <p>{markerEvidence[evidenceKeys[key]].headline}</p>
                    <p className="mt-1 text-slate-500">{markerEvidence[evidenceKeys[key]].detail}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
