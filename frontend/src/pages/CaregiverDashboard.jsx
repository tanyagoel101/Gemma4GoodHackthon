import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  createLifeEvent,
  downloadPdf,
  getBaseline,
  getCorrelations,
  getLifeEvents,
  getPatients,
  getSessions,
  getWeeklySummary,
} from "../api/client";
import CorrelationInsights from "../components/CorrelationInsights";
import LifeEventForm from "../components/LifeEventForm";
import MarkerChart from "../components/MarkerChart";
import TimelineView from "../components/TimelineView";
import WeeklySummary from "../components/WeeklySummary";
import { formatDate, formatDateTime } from "../utils/formatters";

const charts = [
  ["ttr_score", "Vocabulary Variety", 1],
  ["mlu_score", "Sentence Length", 20],
  ["filler_density", "Filler Density", 12],
  ["idea_density", "Idea Density", 1],
  ["referential_cohesion", "Referential Cohesion", 1],
  ["semantic_coherence", "Semantic Coherence", 10],
];

export default function CaregiverDashboard() {
  const { patientId } = useParams();
  const [patient, setPatient] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [baseline, setBaseline] = useState(null);
  const [weeklySummary, setWeeklySummary] = useState(null);
  const [dashboardError, setDashboardError] = useState("");
  const [summaryError, setSummaryError] = useState("");
  const [loadingDashboard, setLoadingDashboard] = useState(true);
  const [loadingSummary, setLoadingSummary] = useState(true);
  const [events, setEvents] = useState([]);
  const [correlations, setCorrelations] = useState(null);
  const [savingEvent, setSavingEvent] = useState(false);

  useEffect(() => {
    setLoadingDashboard(true);
    setDashboardError("");
    Promise.all([getPatients(), getSessions(patientId), getBaseline(patientId), getLifeEvents(patientId), getCorrelations(patientId)])
      .then(([patients, sessionRows, baselineRow, eventRows, correlationRows]) => {
        setPatient(patients.find((entry) => entry.id === patientId) ?? null);
        setSessions(sessionRows);
        setBaseline(baselineRow);
        setEvents(eventRows);
        setCorrelations(correlationRows);
      })
      .catch((error) => {
        setDashboardError(error?.response?.data?.detail ?? "VoiceTrace could not load this dashboard.");
      })
      .finally(() => setLoadingDashboard(false));
  }, [patientId]);

  useEffect(() => {
    setLoadingSummary(true);
    setSummaryError("");
    getWeeklySummary(patientId)
      .then((summaryRow) => {
        setWeeklySummary(summaryRow);
      })
      .catch((error) => {
        setSummaryError(
          error?.response?.data?.detail ??
            "The weekly summary is still generating locally. The rest of the dashboard is ready below.",
        );
      })
      .finally(() => setLoadingSummary(false));
  }, [patientId]);

  const handlePdf = async () => {
    const blob = await downloadPdf(patientId);
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${patient?.name ?? "voicetrace"}-report.pdf`;
    link.click();
    window.URL.revokeObjectURL(url);
  };

  const latestSession = sessions[0];
  const handleSaveEvent = async (payload) => {
    setSavingEvent(true);
    try {
      await createLifeEvent(patientId, payload);
      const [eventRows, correlationRows] = await Promise.all([getLifeEvents(patientId), getCorrelations(patientId)]);
      setEvents(eventRows);
      setCorrelations(correlationRows);
    } finally {
      setSavingEvent(false);
    }
  };

  return (
    <div className="space-y-8">
      <section className="glass-card p-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm uppercase tracking-[0.2em] text-teal-700">Caregiver Dashboard</p>
            <h2 className="mt-2 text-3xl font-semibold text-ink">{patient?.name}</h2>
            <p className="mt-2 text-slate-600">Monitoring since {patient?.created_at ? formatDate(patient.created_at) : "..."}</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link className="rounded-full bg-sky-100 px-5 py-3 font-medium text-ink" to={`/patients/${patientId}/record`}>
              Record New Entry
            </Link>
            <button className="rounded-full bg-ink px-5 py-3 font-medium text-white" onClick={handlePdf} type="button">
              Share with Doctor
            </button>
          </div>
        </div>
      </section>

      <WeeklySummary summary={weeklySummary} loading={loadingSummary} />
      {summaryError && <p className="rounded-3xl bg-ambersoft px-5 py-4 text-slate-700">{summaryError}</p>}

      {dashboardError && <p className="rounded-3xl bg-coralsoft px-5 py-4 text-slate-700">{dashboardError}</p>}
      {loadingDashboard && <p className="rounded-3xl bg-white/80 px-5 py-4 text-slate-700">Loading charts and recent sessions...</p>}

      {latestSession && (
        <section className="grid gap-4 lg:grid-cols-4">
          <article className="glass-card p-5">
            <p className="text-sm uppercase tracking-[0.15em] text-teal-700">This Week at a Glance</p>
            <p className="mt-3 text-slate-700">{latestSession.caregiver_insight}</p>
          </article>
          <article className="glass-card p-5">
            <p className="text-sm uppercase tracking-[0.15em] text-teal-700">Strongest Change</p>
            <p className="mt-3 text-slate-700">{(JSON.parse(latestSession.baseline_deviation_json || "{}").filler_density ?? 0) > 10 ? "Filler phrases are the clearest recent shift." : "No single marker is moving sharply right now."}</p>
          </article>
          <article className="glass-card p-5">
            <p className="text-sm uppercase tracking-[0.15em] text-teal-700">Confidence</p>
            <p className="mt-3 text-slate-700 capitalize">{latestSession.confidence_level} confidence based on recent recording consistency.</p>
          </article>
          <article className="glass-card p-5">
            <p className="text-sm uppercase tracking-[0.15em] text-teal-700">Stable Markers</p>
            <p className="mt-3 text-slate-700">{latestSession.trend_direction === "stable" ? "Several markers remain within the expected day-to-day range." : "Watch the timeline below for context around the latest changes."}</p>
          </article>
        </section>
      )}

      <section className="grid gap-6 xl:grid-cols-2">
        {charts.map(([marker, title, max]) => (
          <MarkerChart key={marker} baseline={baseline} events={events} markerKey={marker} max={max} sessions={sessions} title={title} />
        ))}
      </section>

      <div className="grid gap-6 xl:grid-cols-2">
        <CorrelationInsights correlations={correlations} />
        <TimelineView events={events} sessions={sessions} />
      </div>

      <LifeEventForm onSubmit={handleSaveEvent} saving={savingEvent} />

      <section className="glass-card p-6">
        <h3 className="text-xl font-semibold text-ink">Recent Sessions</h3>
        <div className="mt-4 overflow-x-auto">
          <table className="min-w-full text-left">
            <thead className="text-slate-500">
              <tr>
                <th className="pb-3">Date</th>
                <th className="pb-3">Duration</th>
                <th className="pb-3" title="Weighted longitudinal score based on sustained changes.">Composite Score</th>
                <th className="pb-3">Summary</th>
              </tr>
            </thead>
            <tbody>
              {sessions.slice(0, 10).map((session) => (
                <tr className="border-t border-slate-200" key={session.id}>
                  <td className="py-3">{formatDateTime(session.recorded_at)}</td>
                  <td className="py-3">{Math.round(session.duration_seconds)}s</td>
                  <td className="py-3">{Math.round(session.composite_risk_score)}</td>
                  <td className="py-3 text-slate-600">{session.gemma_summary}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
