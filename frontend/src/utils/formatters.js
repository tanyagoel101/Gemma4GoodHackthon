export const formatDate = (value) =>
  new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));

export const formatDateTime = (value) =>
  new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));

export const riskTone = (score) => {
  if (score <= 40) return "bg-emerald-100 text-emerald-800";
  if (score <= 70) return "bg-amber-100 text-amber-800";
  return "bg-rose-100 text-rose-800";
};

export const trendArrow = (trend) => {
  if (trend === "declining") return "↑";
  if (trend === "improving") return "↓";
  return "→";
};

