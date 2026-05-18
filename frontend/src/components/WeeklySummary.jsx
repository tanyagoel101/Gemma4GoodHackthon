export default function WeeklySummary({ summary, loading }) {
  return (
    <section className="glass-card p-6">
      <div className="flex items-center justify-between gap-4">
        <h2 className="text-xl font-semibold text-ink">Weekly Summary</h2>
        {summary?.trend_direction && (
          <span className="rounded-full bg-seafoam px-4 py-2 text-sm font-medium capitalize text-teal-800">
            {summary.trend_direction}
          </span>
        )}
      </div>
      <p className="mt-4 leading-8 text-slate-700">
        {loading ? "Generating this week's summary..." : summary?.summary_text ?? "No weekly summary yet."}
      </p>
    </section>
  );
}

