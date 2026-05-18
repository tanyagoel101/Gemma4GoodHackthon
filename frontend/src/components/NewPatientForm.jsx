import { useState } from "react";

const initialState = {
  name: "",
  age: "",
  location: "",
  caregiver_name: "",
  caregiver_relationship: "",
};

export default function NewPatientForm({ onCreate, saving }) {
  const [form, setForm] = useState(initialState);
  const [error, setError] = useState("");

  const updateField = (key, value) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    if (!form.name || !form.age || !form.location || !form.caregiver_name || !form.caregiver_relationship) {
      setError("Please fill in all profile details before creating the patient.");
      return;
    }

    try {
      await onCreate({
        ...form,
        age: Number(form.age),
      });
      setForm(initialState);
    } catch (submitError) {
      setError(submitError?.response?.data?.detail ?? "VoiceTrace could not create that patient profile.");
    }
  };

  return (
    <form className="glass-card space-y-5 p-6" onSubmit={handleSubmit}>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-teal-700">New Patient Profile</p>
          <h3 className="mt-2 text-2xl font-semibold text-ink">Add someone new to VoiceTrace</h3>
          <p className="mt-2 text-slate-600">Create a profile once, then start guided voice check-ins right away.</p>
        </div>
        <button className="rounded-full bg-ink px-5 py-3 font-medium text-white disabled:bg-slate-400" disabled={saving} type="submit">
          {saving ? "Creating..." : "Create profile"}
        </button>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <label className="text-sm font-medium text-slate-700">
          Patient name
          <input
            className="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3"
            onChange={(event) => updateField("name", event.target.value)}
            placeholder="Margaret Chen"
            value={form.name}
          />
        </label>
        <label className="text-sm font-medium text-slate-700">
          Age
          <input
            className="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3"
            min="1"
            onChange={(event) => updateField("age", event.target.value)}
            placeholder="74"
            type="number"
            value={form.age}
          />
        </label>
        <label className="text-sm font-medium text-slate-700">
          Location
          <input
            className="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3"
            onChange={(event) => updateField("location", event.target.value)}
            placeholder="rural Iowa"
            value={form.location}
          />
        </label>
        <label className="text-sm font-medium text-slate-700">
          Caregiver name
          <input
            className="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3"
            onChange={(event) => updateField("caregiver_name", event.target.value)}
            placeholder="David Chen"
            value={form.caregiver_name}
          />
        </label>
        <label className="text-sm font-medium text-slate-700 md:col-span-2">
          Caregiver relationship
          <input
            className="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3"
            onChange={(event) => updateField("caregiver_relationship", event.target.value)}
            placeholder="son"
            value={form.caregiver_relationship}
          />
        </label>
      </div>

      {error && <p className="rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</p>}
    </form>
  );
}
