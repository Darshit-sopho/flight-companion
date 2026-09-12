import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

// recharts' ResponsiveContainer needs real layout measurement jsdom doesn't provide — mocked so this
// test focuses on the stats/labels the component computes, not the chart rendering itself.
vi.mock("recharts", () => ({
  ResponsiveContainer: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  BarChart: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  Bar: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
}));

import type { FlightHistoryResponse } from "../../src/api/client";
import { DelayTrendChart } from "../../src/components/DelayTrendChart";

describe("DelayTrendChart", () => {
  it("shows a message when there's no history yet", () => {
    render(
      <DelayTrendChart
        history={{
          flight_id: "x",
          on_time_percentage: null,
          average_delay_minutes: null,
          trend: "stable",
          occurrences: [],
        }}
      />,
    );
    expect(screen.getByText(/No history available/)).toBeInTheDocument();
  });

  it("shows on-time percentage, average delay, and trend direction", () => {
    const history: FlightHistoryResponse = {
      flight_id: "x",
      on_time_percentage: 75,
      average_delay_minutes: 13.8,
      trend: "improving",
      occurrences: [
        { date: "2026-09-05", delay_minutes: 5, on_time: true },
        { date: "2026-08-29", delay_minutes: 32, on_time: false },
      ],
    };

    render(<DelayTrendChart history={history} />);

    expect(screen.getByText("75%")).toBeInTheDocument();
    expect(screen.getByText("13.8m")).toBeInTheDocument();
    expect(screen.getByText(/Improving/)).toBeInTheDocument();
  });
});
