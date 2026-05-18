import { useEffect, useState } from "react";
import { createPatient, getClinicianPatients } from "../api/client";
import NewPatientForm from "../components/NewPatientForm";
import PatientCard from "../components/PatientCard";

export default function CaregiverHome() {
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [savingPatient, setSavingPatient] = useState(false);

  const loadPatients = () => {
    setLoading(true);
    getClinicianPatients()
      .then(setPatients)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadPatients();
  }, []);

  const handleCreatePatient = async (payload) => {
    setSavingPatient(true);
    try {
      await createPatient(payload);
      loadPatients();
    } finally {
      setSavingPatient(false);
    }
  };

  return (
    <div className="space-y-8">
      <section className="glass-card overflow-hidden p-8">
        <div className="max-w-3xl">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-teal-700">Caregiver App</p>
          <h2 className="mt-3 text-4xl font-semibold text-ink">A gentle daily check-in for families tracking speech changes over time.</h2>
          <p className="mt-4 leading-8 text-slate-700">
            Record a short voice diary, review trends against each person&apos;s own baseline, and share a calm summary with their doctor when needed.
          </p>
        </div>
      </section>

      <NewPatientForm onCreate={handleCreatePatient} saving={savingPatient} />

      <section className="grid gap-6 lg:grid-cols-2">
        {loading ? <p>Loading patients...</p> : patients.map((patient) => <PatientCard key={patient.id} patient={patient} />)}
      </section>
    </div>
  );
}
