export default function CorrelationInsights({ correlations, title = "Life Events & Voice" }) {
  return (
    <section className="glass-card p-6">
      <div className="flex items-center justify-between gap-4">
        <h3 className="text-xl font-semibold text-ink">{title}</h3>
        {correlations?.confidence && (
          <span className="rounded-full bg-white px-3 py-2 text-sm font-medium capitalize text-slate-700 shadow-calm">
            {correlations.confidence} confidence
          </span>
        )}
      </div>
      <div className="mt-4 space-y-3">
        {(correlations?.findings ?? []).map((finding) => (
          <p className="rounded-2xl bg-slate-50 px-4 py-3 leading-7 text-slate-700" key={finding}>
            {finding}
          </p>
        ))}
      </div>
      {correlations?.note && <p className="mt-4 text-sm leading-6 text-slate-500">{correlations.note}</p>}
    </section>
  );
}

