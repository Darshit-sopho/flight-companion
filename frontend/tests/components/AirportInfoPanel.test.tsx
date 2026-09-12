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

  it("renders local time in the airport's own timezone, not the viewer's browser timezone", () => {
    // Regression test: the same instant, formatted for two airports an hour apart in timezone, must
    // show two DIFFERENT clock times. Passing `undefined` as the Intl timeZone silently formats in
    // whatever zone the runtime happens to be in instead — that bug showed both airports displaying
    // the identical wall-clock time regardless of which zone they're actually in.
    const instant = "2026-09-12T16:23:00Z"; // 1 hour apart: America/New_York vs America/Halifax

    const { unmount } = render(
      <AirportInfoPanel
        label="Departure"
        loading={false}
        airport={{
          code: "KEWR",
          name: "Newark Liberty Intl",
          city: "Newark",
          country: "US",
          timezone: "America/New_York",
          local_time: instant,
        }}
      />,
    );
    const newYorkTime = screen.getByText(/Local time:/).textContent;
    unmount();

    render(
      <AirportInfoPanel
        label="Arrival"
        loading={false}
        airport={{
          code: "CYHZ",
          name: "Halifax Int'l",
          city: "Halifax",
          country: "CA",
          timezone: "America/Halifax",
          local_time: instant,
        }}
      />,
    );
    const halifaxTime = screen.getByText(/Local time:/).textContent;

    expect(newYorkTime).not.toEqual(halifaxTime);
  });
});
