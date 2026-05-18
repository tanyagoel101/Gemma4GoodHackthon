export default function ReferralLetter({ content, loading, onCopy }) {
  return (
    <section className="glass-card p-6">
      <div className="flex items-center justify-between gap-4">
        <h3 className="text-xl font-semibold text-ink">Referral Letter</h3>
        <button className="rounded-full bg-slate-900 px-4 py-2 text-sm font-medium text-white" onClick={onCopy} type="button">
          Copy
        </button>
      </div>
      <pre className="mt-4 whitespace-pre-wrap font-sans leading-8 text-slate-700">
        {loading ? "Generating referral letter..." : content || "Enter a GP name to generate the referral letter."}
      </pre>
    </section>
  );
}

