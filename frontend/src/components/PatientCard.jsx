import { Link } from "react-router-dom";
import { formatDate, riskTone, trendArrow } from "../utils/formatters";

export default function PatientCard({ patient }) {
  return (
    <article className="glass-card p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h3 className="text-2xl font-semibold text-ink">{patient.name}</h3>
          <p className="mt-1 text-slate-600">
            {patient.age} • {patient.location}
          </p>
          <p className="mt-2 text-slate-500">
            Caregiver: {patient.caregiver_name} ({patient.caregiver_relationship})
          </p>
        </div>
        {patient.latest_composite_risk_score !== undefined && patient.latest_composite_risk_score !== null ? (
          <div className={`rounded-full px-4 py-2 text-sm font-semibold ${riskTone(patient.latest_composite_risk_score)}`}>
            Risk {Math.round(patient.latest_composite_risk_score)}
          </div>
        ) : null}
      </div>
      <div className="mt-6 flex items-center justify-between">
        <div className="text-slate-600">
          <p>Trend {trendArrow(patient.trend_direction)} {patient.trend_direction}</p>
          {patient.last_entry_at ? <p>Last entry {formatDate(patient.last_entry_at)}</p> : <p>No entries yet</p>}
        </div>
        <div className="flex gap-3">
          <Link className="rounded-full bg-sky-100 px-4 py-2 font-medium text-ink" to={`/patients/${patient.id}/dashboard`}>
            Dashboard
          </Link>
          <Link className="rounded-full bg-ink px-4 py-2 font-medium text-white" to={`/patients/${patient.id}/record`}>
            Record
          </Link>
        </div>
      </div>
    </article>
  );
}

