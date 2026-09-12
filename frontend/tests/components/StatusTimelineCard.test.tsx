import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { FlightStatusResponse } from "../../src/api/client";
import { StatusTimelineCard } from "../../src/components/StatusTimelineCard";

const baseStatus: FlightStatusResponse = {
  flight_id: "UAL123-2026-09-12",
  ident: "UAL123",
  status: "active",
  origin: { code: "SFO", gate: "A12", terminal: "2" },
  destination: { code: "ORD", gate: null, terminal: "1" },
  scheduled_departure: "2026-09-12T14:30:00Z",
  estimated_departure: "2026-09-12T14:45:00Z",
  actual_departure: "2026-09-12T14:47:00Z",
  scheduled_arrival: "2026-09-12T20:10:00Z",
  estimated_arrival: "2026-09-12T20:22:00Z",
  actual_arrival: null,
  delay_minutes: 12,
  aircraft: { registration: "N12345", type: "B738" },
};

describe("StatusTimelineCard", () => {
  it("renders ident and both legs' airport codes", () => {
    render(<StatusTimelineCard status={baseStatus} />);
    expect(screen.getByText(/UAL123/)).toBeInTheDocument();
    expect(screen.getByText("SFO")).toBeInTheDocument();
    expect(screen.getByText("ORD")).toBeInTheDocument();
  });

  it("shows 'not yet available' for a field AeroAPI hasn't populated (FR2.5)", () => {
    render(<StatusTimelineCard status={baseStatus} />);
    expect(screen.getAllByText(/not yet available/).length).toBeGreaterThan(0);
  });

  it("shows an on-time badge for a small delay", () => {
    render(<StatusTimelineCard status={{ ...baseStatus, delay_minutes: 5 }} />);
    expect(screen.getByText(/On time/)).toBeInTheDocument();
  });

  it("shows the delay minutes for a large delay", () => {
    render(<StatusTimelineCard status={{ ...baseStatus, delay_minutes: 60 }} />);
    expect(screen.getByText(/Delayed 60m/)).toBeInTheDocument();
  });
});
