import { formatDateTime } from "../utils/formatters";

export default function TimelineView({ sessions = [], events = [] }) {
  const items = [
    ...sessions.slice(0, 8).map((session) => ({
      type: "recording",
      date: session.recorded_at,
      title: "Voice recording",
      detail: session.caregiver_insight || session.gemma_summary,
    })),
    ...events.slice(0, 8).map((event) => ({
      type: "event",
      date: event.event_date,
      title: event.doctor_visit ? "Doctor visit" : "Daily context note",
      detail: event.freeform_notes || `Sleep ${event.sleep_quality}/5 • Stress ${event.stress_level}/5`,
    })),
  ].sort((left, right) => new Date(right.date) - new Date(left.date));

  return (
    <section className="glass-card p-6">
      <h3 className="text-xl font-semibold text-ink">Timeline View</h3>
      <div className="mt-4 space-y-4">
        {items.length ? items.map((item, index) => (
          <div className="flex gap-4" key={`${item.type}-${item.date}-${index}`}>
            <div className={`mt-1 h-3 w-3 rounded-full ${item.type === "recording" ? "bg-teal-500" : "bg-amber-400"}`} />
            <div>
              <p className="font-medium text-ink">{item.title}</p>
              <p className="text-sm text-slate-500">{formatDateTime(item.date)}</p>
              <p className="mt-1 text-slate-700">{item.detail}</p>
            </div>
          </div>
        )) : <p className="text-slate-600">Timeline entries will appear here as recordings and life events are added.</p>}
      </div>
    </section>
  );
}

