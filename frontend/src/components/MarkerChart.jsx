import {
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LineElement,
  LinearScale,
  PointElement,
  Tooltip,
} from "chart.js";
import { Line } from "react-chartjs-2";

ChartJS.register(CategoryScale, LinearScale, LineElement, PointElement, Tooltip, Legend, Filler);

export default function MarkerChart({ title, sessions, baseline, markerKey, max = 10, events = [] }) {
  const recent = [...sessions].slice(0, 60).reverse();
  const labels = recent.map((session) => new Date(session.recorded_at).toLocaleDateString("en-US", { month: "short", day: "numeric" }));
  const scores = recent.map((session) => session[markerKey]);
  const baselineValue = baseline?.markers?.[markerKey] ?? 0;
  const rollingValues = recent.map((session, index) => {
    const window = recent.slice(Math.max(0, index - 6), index + 1);
    return window.reduce((sum, item) => sum + Number(item[markerKey] ?? 0), 0) / window.length;
  });
  const eventMarkers = labels.map((label) =>
    events.some((event) => new Date(event.event_date).toLocaleDateString("en-US", { month: "short", day: "numeric" }) === label)
      ? max * 0.95
      : null,
  );

  const data = {
    labels,
    datasets: [
      {
        label: title,
        data: scores,
        borderColor: "#0f766e",
        backgroundColor: "rgba(15,118,110,0.12)",
        fill: false,
        pointRadius: scores.map((score) =>
          baselineValue && Math.abs(score - baselineValue) / baselineValue > 0.2 ? 6 : 4,
        ),
        pointBackgroundColor: scores.map((score) =>
          baselineValue && Math.abs(score - baselineValue) / baselineValue > 0.2 ? "#f59e0b" : "#0f766e",
        ),
        tension: 0.35,
      },
      {
        label: "Baseline",
        data: scores.map(() => baselineValue),
        borderColor: "rgba(59,130,246,0.4)",
        backgroundColor: "rgba(59,130,246,0.1)",
        fill: 1,
        pointRadius: 0,
        tension: 0,
      },
      {
        label: "Baseline Band",
        data: scores.map(() => baselineValue * 1.2),
        borderColor: "rgba(59,130,246,0)",
        backgroundColor: "rgba(59,130,246,0.08)",
        pointRadius: 0,
        tension: 0,
      },
      {
        label: "Rolling Average",
        data: rollingValues,
        borderColor: "#1d4ed8",
        backgroundColor: "rgba(29,78,216,0.08)",
        borderDash: [6, 4],
        pointRadius: 0,
        tension: 0.25,
      },
      {
        label: "Life Events",
        data: eventMarkers,
        pointRadius: 6,
        pointHoverRadius: 7,
        showLine: false,
        pointBackgroundColor: "#f59e0b",
      },
    ],
  };

  return (
    <div className="glass-card p-6">
      <h3 className="text-lg font-semibold text-ink" title="Trend chart with baseline band, rolling average, and highlighted deviations.">{title}</h3>
      <div className="mt-4 h-72">
        <Line
          data={data}
          options={{
            maintainAspectRatio: false,
            responsive: true,
            scales: {
              y: {
                suggestedMin: 0,
                suggestedMax: max,
              },
            },
            plugins: {
              legend: { display: false },
            },
          }}
        />
      </div>
    </div>
  );
}
