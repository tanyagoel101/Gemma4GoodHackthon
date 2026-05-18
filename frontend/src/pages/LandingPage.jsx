import { Link } from "react-router-dom";

const pillars = [
  {
    eyebrow: "What VoiceTrace Does",
    title: "Turns short daily voice diaries into understandable longitudinal insights.",
    body:
      "VoiceTrace records a familiar check-in, transcribes it locally, measures speech and voice patterns over time, and translates those changes into clear summaries for families and clinicians.",
  },
  {
    eyebrow: "Why It Matters",
    title: "Subtle communication changes often show up long before a formal diagnosis conversation.",
    body:
      "Instead of comparing someone to a population average, VoiceTrace compares each person to their own baseline. That makes it much easier to notice meaningful drift without overreacting to a single off day.",
  },
  {
    eyebrow: "Why Local-First Helps",
    title: "Everything stays on the device so caregivers can use it with more confidence.",
    body:
      "Audio, transcripts, trend data, and summaries are processed locally on the Mac. That supports privacy, lowers barriers to use, and makes the tool more practical in rural or bandwidth-limited settings.",
  },
];

const benefits = [
  "Daily reflection prompts that encourage richer, more consistent recordings",
  "Warm caregiver summaries that explain what changed in plain language",
  "Clinician-facing trend views, confidence indicators, and exportable reports",
  "Life event journaling to connect speech changes with sleep, stress, illness, or routines",
];

export default function LandingPage() {
  return (
    <div className="space-y-8">
      <section className="relative overflow-hidden rounded-[2rem] border border-white/70 bg-white/80 px-8 py-10 shadow-calm backdrop-blur md:px-12 md:py-14">
        <div className="absolute inset-x-0 top-0 h-40 bg-gradient-to-r from-sky-200/60 via-teal-100/40 to-emerald-100/60" />
        <div className="relative grid gap-10 xl:grid-cols-[1.2fr_0.8fr]">
          <div className="max-w-3xl">
            <p className="text-sm font-semibold uppercase tracking-[0.25em] text-teal-700">VoiceTrace</p>
            <h2 className="mt-4 max-w-3xl text-4xl font-semibold leading-tight text-ink md:text-5xl">
              A local-first cognitive monitoring companion built around the story in someone&apos;s speech.
            </h2>
            <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-700">
              VoiceTrace helps families and clinicians observe communication patterns over time through short recorded diaries,
              longitudinal voice markers, and gentle AI-generated interpretations designed for supportive monitoring.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link className="rounded-full bg-ink px-6 py-3 font-medium text-white shadow-calm" to="/caregiver">
                Open Caregiver App
              </Link>
              <Link className="rounded-full bg-white px-6 py-3 font-medium text-ink shadow-calm" to="/clinician">
                Open Clinician Dashboard
              </Link>
            </div>
            <div className="mt-8 flex flex-wrap gap-3 text-sm text-slate-600">
              <span className="rounded-full bg-sky-50 px-4 py-2">All data stays on this device</span>
              <span className="rounded-full bg-emerald-50 px-4 py-2">Built for longitudinal monitoring</span>
              <span className="rounded-full bg-amber-50 px-4 py-2">Supportive, non-diagnostic framing</span>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-1">
            <article className="glass-card p-6">
              <p className="text-sm uppercase tracking-[0.2em] text-teal-700">For Caregivers</p>
              <h3 className="mt-3 text-2xl font-semibold text-ink">Gentle daily check-ins</h3>
              <p className="mt-3 leading-7 text-slate-700">
                Record a brief diary, log life events, and review changes with calm explanations instead of raw numbers alone.
              </p>
            </article>
            <article className="glass-card p-6">
              <p className="text-sm uppercase tracking-[0.2em] text-teal-700">For Clinicians</p>
              <h3 className="mt-3 text-2xl font-semibold text-ink">Longitudinal evidence at a glance</h3>
              <p className="mt-3 leading-7 text-slate-700">
                Review baseline comparisons, rolling trends, acoustic summaries, contextual correlations, and printable visit briefs.
              </p>
            </article>
          </div>
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-3">
        {pillars.map((pillar) => (
          <article className="glass-card p-7" key={pillar.title}>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-teal-700">{pillar.eyebrow}</p>
            <h3 className="mt-3 text-2xl font-semibold leading-snug text-ink">{pillar.title}</h3>
            <p className="mt-4 leading-8 text-slate-700">{pillar.body}</p>
          </article>
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <article className="glass-card p-8">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-teal-700">Why It&apos;s Useful</p>
          <h3 className="mt-3 text-3xl font-semibold text-ink">A monitoring workflow that turns isolated recordings into a richer picture over time.</h3>
          <ul className="mt-6 space-y-4 text-slate-700">
            {benefits.map((benefit) => (
              <li className="flex items-start gap-3" key={benefit}>
                <span className="mt-1 h-2.5 w-2.5 rounded-full bg-teal-500" />
                <span className="leading-7">{benefit}</span>
              </li>
            ))}
          </ul>
        </article>

        <article className="glass-card p-8">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-teal-700">How It Works</p>
          <div className="mt-5 space-y-5">
            {[
              ["1", "Record a short voice diary", "A caregiver or patient responds to a daily reflection prompt or records a freeform check-in."],
              ["2", "Analyze speech locally", "VoiceTrace transcribes the recording, extracts speech and acoustic markers, and compares them to personal baseline patterns."],
              ["3", "Review explainable insights", "Families see plain-language interpretations, while clinicians can explore trends, confidence, reports, and context."],
            ].map(([step, title, body]) => (
              <div className="flex gap-4" key={step}>
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-sky-100 font-semibold text-ink">
                  {step}
                </div>
                <div>
                  <h4 className="text-xl font-semibold text-ink">{title}</h4>
                  <p className="mt-2 leading-7 text-slate-700">{body}</p>
                </div>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="rounded-[2rem] border border-white/70 bg-gradient-to-r from-slate-900 to-sky-900 px-8 py-10 text-white shadow-calm">
        <div className="grid gap-6 lg:grid-cols-[1fr_auto] lg:items-center">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-sky-200">Supportive Monitoring Only</p>
            <h3 className="mt-3 text-3xl font-semibold">VoiceTrace is meant to support observation, not diagnose.</h3>
            <p className="mt-4 max-w-3xl leading-8 text-sky-50/90">
              The platform highlights communication patterns and changes that may be useful to notice, discuss, and share. It should always be interpreted alongside clinical judgment and real-world context.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link className="rounded-full bg-white px-6 py-3 font-medium text-ink" to="/caregiver">
              Start Recording
            </Link>
            <Link className="rounded-full border border-white/30 px-6 py-3 font-medium text-white" to="/clinician">
              Review Trends
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
