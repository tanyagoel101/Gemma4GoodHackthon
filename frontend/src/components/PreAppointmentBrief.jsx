export default function PreAppointmentBrief({ content, loading }) {
  return (
    <section className="glass-card p-6">
      <h3 className="text-xl font-semibold text-ink">Pre-Appointment Brief</h3>
      <pre className="mt-4 whitespace-pre-wrap font-sans leading-8 text-slate-700">
        {loading ? "Generating brief..." : content || "Select a patient and generate a brief."}
      </pre>
    </section>
  );
}

