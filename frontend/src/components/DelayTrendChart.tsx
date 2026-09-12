import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { FlightHistoryResponse } from "../api/client";

interface Props {
  history: FlightHistoryResponse;
}

const TREND_LABEL: Record<FlightHistoryResponse["trend"], string> = {
  improving: "Improving ↓",
  worsening: "Worsening ↑",
  stable: "Stable →",
};

export function DelayTrendChart({ history }: Props) {
  if (history.occurrences.length === 0) {
    return (
      <section className="card" aria-label="Flight history">
        <h2>Recent history</h2>
        <p>No history available for this flight yet.</p>
      </section>
    );
  }

  const chartData = [...history.occurrences].reverse().map((o) => ({
    date: o.date ?? "?",
    delay: o.delay_minutes ?? 0,
  }));

  return (
    <section className="card" aria-label="Flight history">
      <h2>Recent history</h2>
      <div className="history-stats">
        <div>
          <span className="stat-value">{history.on_time_percentage ?? "—"}%</span>
          <span className="stat-label">on time</span>
        </div>
        <div>
          <span className="stat-value">{history.average_delay_minutes ?? "—"}m</span>
          <span className="stat-label">avg delay</span>
        </div>
        <div>
          <span className="stat-value">{TREND_LABEL[history.trend]}</span>
          <span className="stat-label">trend</span>
        </div>
      </div>
      <div style={{ width: "100%", height: 220 }}>
        <ResponsiveContainer>
          <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} unit="m" />
            <Tooltip />
            <Bar dataKey="delay" fill="#4f7cff" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
