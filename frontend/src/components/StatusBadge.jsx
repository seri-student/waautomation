import React from "react";

const STYLES = {
  New: "bg-amber-100 text-amber-800 border-amber-200",
  Confirmed: "bg-sky-100 text-sky-800 border-sky-200",
  Preparing: "bg-orange-100 text-orange-800 border-orange-200",
  Ready: "bg-emerald-100 text-emerald-800 border-emerald-200",
  "Out for Delivery": "bg-teal-100 text-teal-800 border-teal-200",
  Delivered: "bg-stone-200 text-stone-700 border-stone-300",
  Cancelled: "bg-rose-100 text-rose-800 border-rose-200",
};

const CONN = {
  connected: "bg-emerald-100 text-emerald-700 border-emerald-200",
  connecting: "bg-amber-100 text-amber-700 border-amber-200",
  disconnected: "bg-stone-200 text-stone-600 border-stone-300",
  error: "bg-rose-100 text-rose-700 border-rose-200",
};

export function StatusBadge({ status, testId }) {
  const cls = STYLES[status] || "bg-stone-100 text-stone-700 border-stone-200";
  return (
    <span
      data-testid={testId || `status-badge-${status}`}
      className={`inline-flex items-center border px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wide ${cls}`}
    >
      {status}
    </span>
  );
}

export function ConnectionBadge({ status, testId }) {
  const s = (status || "disconnected").toLowerCase();
  const cls = CONN[s] || CONN.disconnected;
  return (
    <span
      data-testid={testId || "connection-badge"}
      className={`inline-flex items-center gap-1.5 border px-2.5 py-1 rounded-full text-xs font-semibold ${cls}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${s === "connected" ? "bg-emerald-500 animate-pulse" : s === "connecting" ? "bg-amber-500 animate-pulse" : s === "error" ? "bg-rose-500" : "bg-stone-400"}`} />
      {s.charAt(0).toUpperCase() + s.slice(1)}
    </span>
  );
}
