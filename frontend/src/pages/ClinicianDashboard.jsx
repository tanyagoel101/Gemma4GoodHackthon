import { useEffect, useState } from "react";
import {
  downloadPdf,
  getBaseline,
  getBrief,
  getClinicianPatients,
  getCorrelations,
  getReferral,
  getSessions,
} from "../api/client";
import CorrelationInsights from "../components/CorrelationInsights";
import MarkerChart from "../components/MarkerChart";
import PreAppointmentBrief from "../components/PreAppointmentBrief";
import ReferralLetter from "../components/ReferralLetter";
import { formatDate, riskTone, trendArrow } from "../utils/formatters";

const charts = [
  ["ttr_score", "Type-Token Ratio", 1],
  ["mlu_score", "Mean Length of Utterance", 20],
  ["filler_density", "Filler Words per 100", 12],
  ["idea_density", "Idea Density", 1],
  ["referential_cohesion", "Pronoun-to-Noun Ratio", 1],
  ["semantic_coherence", "Semantic Coherence", 10],
];

export default function ClinicianDashboard() {
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [baseline, setBaseline] = useState(null);
  const [brief, setBrief] = useState("");
  const [referral, setReferral] = useState("");
  const [gpName, setGpName] = useState("");
  const [loadingBrief, setLoadingBrief] = useState(false);
  const [loadingReferral, setLoadingReferral] = useState(false);
  const [correlations, setCorrelations] = useState(null);

  useEffect(() => {
    getClinicianPatients().then((rows) => {
      setPatients(rows);
      if (rows[0]) setSelectedPatient(rows[0]);
    });
  }, []);

  useEffect(() => {
    if (!selectedPatient) return;
    Promise.all([getSessions(selectedPatient.id), getBaseline(selectedPatient.id), getCorrelations(selectedPatient.id)]).then(([sessionRows, baselineRow, correlationRows]) => {
      setSessions(sessionRows);
      setBaseline(baselineRow);
      setCorrelations(correlationRows);
    });
  }, [selectedPatient]);

  const handleBrief = async (patientId) => {
    setLoadingBrief(true);
    try {
      const data = await getBrief(patientId);
      setBrief(data.content);
    } finally {
      setLoadingBrief(false);
    }
  };

  const handleReferral = async (patientId) => {
    if (!gpName.trim()) return;
    setLoadingReferral(true);
    try {
      const data = await getReferral(patientId, gpName);
      setReferral(data.content);
    } finally {
      setLoadingReferral(false);
    }
  };

  const handleCopy = async () => {
    if (referral) await navigator.clipboard.writeText(referral);
  };

  const handlePdf = async () => {
    if (!selectedPatient) return;
    const blob = await downloadPdf(selectedPatient.id);
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${selectedPatient.name}-report.pdf`;
    link.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-8">
      <section className="glass-card border-l-8 border-amber-400 p-8">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-amber-700">Clinician Dashboard</p>
        <div className="mt-3 flex flex-wrap items-center justify-between gap-4">
          <h2 className="text-3xl font-semibold text-ink">Patient Overview</h2>
          <span className="rounded-full bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-calm">
            {patients.length} patients
          </span>
        </div>
        <p className="mt-4 leading-8 text-slate-700">
          VoiceTrace provides linguistic trend data for clinical support only. It is not a diagnostic tool and does not replace clinical assessment.
        </p>
        <p className="mt-2 text-slate-500">
          For clinical support only. Not a diagnostic tool. Requires physician review. Not a substitute for specialist assessment.
        </p>
      </section>

      <section className="glass-card p-6">
        <div className="overflow-x-auto">
          <table className="min-w-full text-left">
            <thead>
              <tr className="text-slate-500">
                <th className="pb-3">Name</th>
                <th className="pb-3">Age</th>
                <th className="pb-3">Location</th>
                <th className="pb-3">Latest Risk</th>
                <th className="pb-3">Trend</th>
                <th className="pb-3">Last Entry</th>
                <th className="pb-3">Sessions</th>
                <th className="pb-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {patients.map((patient) => (
                <tr className="border-t border-slate-200" key={patient.id}>
                  <td className="py-4 font-medium text-ink">{patient.name}</td>
                  <td className="py-4">{patient.age}</td>
                  <td className="py-4">{patient.location}</td>
                  <td className="py-4">
                    {patient.latest_composite_risk_score !== null ? (
                      <span className={`rounded-full px-3 py-1 text-sm font-semibold ${riskTone(patient.latest_composite_risk_score)}`}>
                        {Math.round(patient.latest_composite_risk_score)}
                      </span>
                    ) : (
                      "N/A"
                    )}
                  </td>
                  <td className="py-4">
                    {trendArrow(patient.trend_direction)} {patient.trend_direction}
                  </td>
                  <td className="py-4">{patient.last_entry_at ? formatDate(patient.last_entry_at) : "No entries"}</td>
                  <td className="py-4">{patient.total_sessions}</td>
                  <td className="py-4">
                    <div className="flex flex-wrap gap-2">
                      <button className="rounded-full bg-sky-100 px-3 py-2 text-sm font-medium text-ink" onClick={() => { setSelectedPatient(patient); handleBrief(patient.id); }} type="button">
                        View Brief
                      </button>
                      <button className="rounded-full bg-white px-3 py-2 text-sm font-medium text-ink shadow-calm" onClick={() => setSelectedPatient(patient)} type="button">
                        Charts
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {selectedPatient && (
        <>
          <section className="glass-card p-8">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <p className="text-sm uppercase tracking-[0.2em] text-teal-700">Selected Patient</p>
                <h3 className="mt-2 text-3xl font-semibold text-ink">{selectedPatient.name}</h3>
              </div>
              <button className="rounded-full bg-ink px-4 py-3 font-medium text-white" onClick={handlePdf} type="button">
                Download PDF
              </button>
            </div>
          </section>

          <section className="grid gap-6 xl:grid-cols-2">
            {charts.map(([marker, title, max]) => (
              <MarkerChart key={marker} baseline={baseline} markerKey={marker} max={max} sessions={sessions} title={title} />
            ))}
          </section>

          {sessions[0] && (
            <section className="grid gap-4 lg:grid-cols-4">
              <article className="glass-card p-5">
                <p className="text-sm uppercase tracking-[0.15em] text-teal-700">Longitudinal Summary</p>
                <p className="mt-3 text-slate-700">{sessions[0].clinician_insight}</p>
              </article>
              <article className="glass-card p-5">
                <p className="text-sm uppercase tracking-[0.15em] text-teal-700">Trend Velocity</p>
                <p className="mt-3 text-slate-700 capitalize">{sessions[0].trend_direction} over the most recent window.</p>
              </article>
              <article className="glass-card p-5">
                <p className="text-sm uppercase tracking-[0.15em] text-teal-700">Confidence</p>
                <p className="mt-3 text-slate-700 capitalize">{sessions[0].confidence_level} confidence.</p>
              </article>
              <article className="glass-card p-5">
                <p className="text-sm uppercase tracking-[0.15em] text-teal-700">Acoustic Snapshot</p>
                <p className="mt-3 text-slate-700">
                  {Math.round(sessions[0].words_per_minute)} wpm • pause freq {sessions[0].pause_frequency?.toFixed?.(1) ?? "0.0"}
                </p>
              </article>
            </section>
          )}

          <div className="grid gap-6 xl:grid-cols-2">
            <PreAppointmentBrief content={brief} loading={loadingBrief} />
            <div className="space-y-4">
              <div className="glass-card p-6">
                <h3 className="text-xl font-semibold text-ink">Generate Referral Letter</h3>
                <div className="mt-4 flex flex-wrap gap-3">
                  <input
                    className="min-w-[240px] flex-1 rounded-full border border-slate-200 px-4 py-3"
                    onChange={(event) => setGpName(event.target.value)}
                    placeholder="Enter referring GP name"
                    value={gpName}
                  />
                  <button
                    className="rounded-full bg-ink px-5 py-3 font-medium text-white"
                    onClick={() => handleReferral(selectedPatient.id)}
                    type="button"
                  >
                    Generate Referral
                  </button>
                </div>
              </div>
              <ReferralLetter content={referral} loading={loadingReferral} onCopy={handleCopy} />
            </div>
          </div>

          <CorrelationInsights correlations={correlations} title="Context Correlations" />
        </>
      )}
    </div>
  );
}
