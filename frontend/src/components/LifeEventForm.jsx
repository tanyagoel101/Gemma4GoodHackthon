import { useState } from "react";

const initialState = {
  event_date: new Date().toISOString().slice(0, 10),
  sleep_quality: 3,
  stress_level: 3,
  illness: false,
  medication_change: false,
  missed_meals: false,
  social_activity: 3,
  doctor_visit: false,
  freeform_notes: "",
};

const scaleLabels = {
  sleep_quality: [
    ["1", "Very poor"],
    ["2", "Not great"],
    ["3", "Okay"],
    ["4", "Good"],
    ["5", "Very good"],
  ],
  stress_level: [
    ["1", "Very calm"],
    ["2", "Mostly calm"],
    ["3", "Mixed day"],
    ["4", "More stressful"],
    ["5", "Very stressful"],
  ],
  social_activity: [
    ["1", "Very little"],
    ["2", "A little"],
    ["3", "Some"],
    ["4", "Quite a bit"],
    ["5", "A lot"],
  ],
};

function ChoiceScale({ field, label, onChange, value }) {
  return (
    <div className="space-y-3">
      <p className="text-base font-medium text-slate-700">{label}</p>
      <div className="grid gap-2 sm:grid-cols-5">
        {scaleLabels[field].map(([score, text]) => (
          <button
            className={`rounded-2xl border px-4 py-4 text-left transition ${
              Number(value) === Number(score)
                ? "border-teal-500 bg-seafoam text-teal-900"
                : "border-slate-200 bg-white text-slate-700"
            }`}
            key={score}
            onClick={() => onChange(field, Number(score))}
            type="button"
          >
            <span className="block text-lg font-semibold">{score}</span>
            <span className="mt-1 block text-sm">{text}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

function ToggleChip({ checked, label, onChange }) {
  return (
    <button
      aria-pressed={checked}
      className={`rounded-2xl border px-4 py-4 text-left transition ${
        checked ? "border-amber-400 bg-ambersoft text-amber-900" : "border-slate-200 bg-white text-slate-700"
      }`}
      onClick={onChange}
      type="button"
    >
      <span className="block text-sm font-semibold">{label}</span>
      <span className="mt-1 block text-sm">{checked ? "Marked for this day" : "Tap if this applied today"}</span>
    </button>
  );
}

export default function LifeEventForm({ onSubmit, saving }) {
  const [form, setForm] = useState(initialState);
  const [error, setError] = useState("");

  const updateField = (key, value) => setForm((current) => ({ ...current, [key]: value }));

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    try {
      await onSubmit(form);
      setForm(initialState);
    } catch (submitError) {
      setError(submitError?.response?.data?.detail ?? "VoiceTrace could not save that context note right now.");
    }
  };

  return (
    <form className="glass-card space-y-5 p-6" onSubmit={handleSubmit}>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h3 className="text-xl font-semibold text-ink">Daily Context Journal</h3>
          <p className="mt-1 text-slate-600">A little context can help explain ordinary day-to-day voice changes.</p>
        </div>
        <button className="rounded-full bg-ink px-4 py-3 text-sm font-medium text-white" disabled={saving} type="submit">
          {saving ? "Saving..." : "Save Context"}
        </button>
      </div>

      <p className="rounded-2xl bg-skywash px-4 py-3 text-sm leading-7 text-slate-700">
        Choose the options that feel closest to the day. It is okay to skip anything you are unsure about.
      </p>

      <div className="grid gap-4 md:grid-cols-2">
        <label className="text-sm font-medium text-slate-700">
          Event date
          <input
            className="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 text-base"
            onChange={(event) => updateField("event_date", event.target.value)}
            type="date"
            value={form.event_date}
          />
        </label>
        <div className="rounded-2xl bg-slate-50 px-4 py-4 text-sm leading-7 text-slate-600">
          Use this journal to add context like sleep, stress, meals, and appointments. VoiceTrace uses these notes only to look for gentle associations over time.
        </div>
      </div>

      <ChoiceScale field="sleep_quality" label="How was sleep quality?" onChange={updateField} value={form.sleep_quality} />
      <ChoiceScale field="stress_level" label="How stressful did the day feel?" onChange={updateField} value={form.stress_level} />
      <ChoiceScale field="social_activity" label="How much social activity was there?" onChange={updateField} value={form.social_activity} />

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {[
          ["illness", "Feeling unwell"],
          ["medication_change", "Medication change"],
          ["missed_meals", "Missed meals"],
          ["doctor_visit", "Doctor visit"],
        ].map(([key, label]) => (
          <ToggleChip
            checked={form[key]}
            key={key}
            label={label}
            onChange={() => updateField(key, !form[key])}
          />
        ))}
      </div>

      <label className="block text-sm font-medium text-slate-700">
        Notes
        <textarea
          className="mt-2 min-h-28 w-full rounded-2xl border border-slate-200 px-4 py-3 text-base"
          onChange={(event) => updateField("freeform_notes", event.target.value)}
          placeholder="Anything else that might help explain the week? For example: travel, a family visit, or a change in routine."
          value={form.freeform_notes}
        />
      </label>

      {error && <p className="rounded-2xl bg-rose-50 px-4 py-3 text-sm leading-7 text-rose-800">{error}</p>}
    </form>
  );
}
