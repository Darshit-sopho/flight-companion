import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AirportInfoPanel } from "../../src/components/AirportInfoPanel";

describe("AirportInfoPanel", () => {
  it("shows a loading state", () => {
    render(<AirportInfoPanel label="Departure" airport={null} loading />);
    expect(screen.getByText("Loading…")).toBeInTheDocument();
  });

  it("shows an unavailable state when not loading and no airport data", () => {
    render(<AirportInfoPanel label="Departure" airport={null} loading={false} />);
    expect(screen.getByText(/unavailable/)).toBeInTheDocument();
  });

  it("renders airport name, city, and code", () => {
    render(
      <AirportInfoPanel
        label="Departure"
        loading={false}
        airport={{
          code: "SFO",
          name: "San Francisco International Airport",
          city: "San Francisco",
          country: "US",
          timezone: "America/Los_Angeles",
          local_time: "2026-09-12T07:30:00-07:00",
        }}
      />,
    );
    expect(screen.getByText("San Francisco International Airport")).toBeInTheDocument();
    expect(screen.getByText(/San Francisco.*SFO/)).toBeInTheDocument();
  });
});
