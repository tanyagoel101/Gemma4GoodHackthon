import { NavLink, Route, Routes } from "react-router-dom";
import CaregiverDashboard from "./pages/CaregiverDashboard";
import CaregiverHome from "./pages/CaregiverHome";
import ClinicianDashboard from "./pages/ClinicianDashboard";
import LandingPage from "./pages/LandingPage";
import RecordDiary from "./pages/RecordDiary";
import { useHealthStatus } from "./hooks/useHealthStatus";

function SetupModal({ message }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/45 p-6">
      <div className="glass-card max-w-xl p-8">
        <h2 className="text-2xl font-semibold text-ink">Local AI Setup Needed</h2>
        <p className="mt-4 leading-8 text-slate-700">{message}</p>
        <ol className="mt-4 list-decimal space-y-2 pl-6 text-slate-700">
          <li>Start Ollama on this Mac.</li>
          <li>Run <code>ollama pull gemma4</code>.</li>
          <li>Restart the backend if you just installed the model.</li>
        </ol>
      </div>
    </div>
  );
}

export default function App() {
  const { health, loading } = useHealthStatus();
  const degraded = !loading && health?.status === "degraded";

  return (
    <div className="min-h-screen">
      <header className="border-b border-white/60 bg-white/70 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-6 py-5">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-teal-700">VoiceTrace</p>
            <h1 className="text-3xl font-semibold text-ink">Local-first speech monitoring for cognitive health</h1>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <span className="rounded-full bg-slate-900 px-4 py-2 text-sm font-medium text-white">
              All data stays on this device
            </span>
            <nav className="flex gap-2 rounded-full bg-white/80 p-2 shadow-calm">
              <NavLink
                className={({ isActive }) =>
                  `rounded-full px-4 py-2 text-sm font-medium ${isActive ? "bg-sky-100 text-ink" : "text-slate-600"}`
                }
                to="/"
              >
                Home
              </NavLink>
              <NavLink
                className={({ isActive }) =>
                  `rounded-full px-4 py-2 text-sm font-medium ${isActive ? "bg-sky-100 text-ink" : "text-slate-600"}`
                }
                to="/caregiver"
              >
                Caregiver
              </NavLink>
              <NavLink
                className={({ isActive }) =>
                  `rounded-full px-4 py-2 text-sm font-medium ${isActive ? "bg-sky-100 text-ink" : "text-slate-600"}`
                }
                to="/clinician"
              >
                Clinician
              </NavLink>
            </nav>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-8">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/caregiver" element={<CaregiverHome />} />
          <Route path="/patients/:patientId/record" element={<RecordDiary health={health} />} />
          <Route path="/patients/:patientId/dashboard" element={<CaregiverDashboard />} />
          <Route path="/clinician" element={<ClinicianDashboard />} />
        </Routes>
      </main>

      {degraded && <SetupModal message={health.message} />}
    </div>
  );
}
