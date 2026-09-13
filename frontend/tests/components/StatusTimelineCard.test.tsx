import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { FlightStatusResponse } from "../../src/api/client";
import { StatusTimelineCard } from "../../src/components/StatusTimelineCard";

const baseStatus: FlightStatusResponse = {
  flight_id: "UAL123-2026-09-12",
  ident: "UAL123",
  status: "active",
  origin: {
    code: "KSFO",
    iata: "SFO",
    name: "San Francisco International Airport",
    city: "San Francisco",
    timezone: "America/Los_Angeles",
    gate: "A12",
    terminal: "2",
  },
  destination: {
    code: "KORD",
    iata: "ORD",
    name: "O'Hare International Airport",
    city: "Chicago",
    timezone: "America/Chicago",
    gate: null,
    terminal: "1",
  },
  scheduled_departure: "2026-09-12T14:30:00Z",
  estimated_departure: "2026-09-12T14:45:00Z",
  actual_departure: "2026-09-12T14:47:00Z",
  scheduled_arrival: "2026-09-12T20:10:00Z",
  estimated_arrival: "2026-09-12T20:22:00Z",
  actual_arrival: null,
  delay_minutes: 12,
  aircraft: { registration: "N12345", type: "B738" },
  operator: { icao: "UAL", iata: "UA", name: "United Airlines" },
  progress_percent: 42,
  flight_duration_minutes: 330,
  route_distance: 1846,
  diverted: null,
};

describe("StatusTimelineCard", () => {
  it("renders ident and both legs' IATA codes", () => {
    render(<StatusTimelineCard status={baseStatus} />);
    expect(screen.getByText(/UAL123/)).toBeInTheDocument();
    expect(screen.getByText("SFO")).toBeInTheDocument();
    expect(screen.getByText("ORD")).toBeInTheDocument();
  });

  it("shows the ICAO code secondarily alongside the IATA code (SC-E2.1)", () => {
    render(<StatusTimelineCard status={baseStatus} />);
    expect(screen.getByText(/SFO · KSFO/)).toBeInTheDocument();
    expect(screen.getByText(/ORD · KORD/)).toBeInTheDocument();
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

  describe("operator line (SC-C1)", () => {
    it("shows the operator's friendly name and ICAO code when present", () => {
      render(<StatusTimelineCard status={baseStatus} />);
      expect(screen.getByText(/Operated by United Airlines \(UAL\)/)).toBeInTheDocument();
    });

    it("falls back to the ICAO code when no friendly name is known", () => {
      render(
        <StatusTimelineCard
          status={{ ...baseStatus, operator: { icao: "ZZZ", iata: null, name: null } }}
        />,
      );
      expect(screen.getByText(/Operated by ZZZ/)).toBeInTheDocument();
    });

    it("renders nothing when there is no operator", () => {
      render(<StatusTimelineCard status={{ ...baseStatus, operator: null }} />);
      expect(screen.queryByText(/Operated by/)).not.toBeInTheDocument();
    });
  });

  describe("duration and distance (SC-C2, SC-C3, SC-E1)", () => {
    it("shows flight duration formatted as hours and minutes", () => {
      render(<StatusTimelineCard status={baseStatus} />);
      expect(screen.getByText("5h 30m")).toBeInTheDocument();
    });

    it("shows trip distance", () => {
      render(<StatusTimelineCard status={baseStatus} />);
      expect(screen.getByText("1,846 mi")).toBeInTheDocument();
    });

    it("omits duration/distance when not available, without erroring", () => {
      render(
        <StatusTimelineCard
          status={{ ...baseStatus, flight_duration_minutes: null, route_distance: null }}
        />,
      );
      expect(screen.queryByText(/mi$/)).not.toBeInTheDocument();
    });
  });

  describe("dynamic Estimated/Actual row (SC-A2, SC-A3)", () => {
    it("shows 'Estimated' when no actual time is known yet", () => {
      const status: FlightStatusResponse = { ...baseStatus, actual_departure: null };
      render(<StatusTimelineCard status={status} />);
      expect(screen.getAllByText("Estimated").length).toBeGreaterThan(0);
    });

    it("shows 'Actual' in place of 'Estimated' once an actual time is known", () => {
      render(<StatusTimelineCard status={baseStatus} />);
      // baseStatus has actual_departure set, so the origin leg's dynamic row is "Actual".
      const actualLabels = screen.getAllByText("Actual");
      expect(actualLabels.length).toBeGreaterThan(0);
    });

    it("shows 'Cancelled' instead of a time when the flight is cancelled", () => {
      render(<StatusTimelineCard status={{ ...baseStatus, status: "cancelled" }} />);
      expect(screen.getAllByText("Cancelled").length).toBe(2); // origin + destination legs
    });
  });

  describe("flight progress bar (SC-A1)", () => {
    it("shows 0% for a scheduled flight regardless of progress_percent", () => {
      render(<StatusTimelineCard status={{ ...baseStatus, status: "scheduled", progress_percent: 55 }} />);
      expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "0");
    });

    it("shows 100% for a landed flight regardless of progress_percent", () => {
      render(<StatusTimelineCard status={{ ...baseStatus, status: "landed", progress_percent: 10 }} />);
      expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "100");
    });

    it("uses the raw progress_percent for an active flight", () => {
      render(<StatusTimelineCard status={{ ...baseStatus, status: "active", progress_percent: 42 }} />);
      expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "42");
    });

    it("hides the progress bar entirely for a cancelled flight", () => {
      render(<StatusTimelineCard status={{ ...baseStatus, status: "cancelled" }} />);
      expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
    });
  });

  describe("timezone mode (SC-B1, SC-B2)", () => {
    it("defaults to each leg's own airport-local time and labels the zone", () => {
      render(<StatusTimelineCard status={baseStatus} />);
      // origin is America/Los_Angeles -> PDT/PST; destination is America/Chicago -> CDT/CST.
      expect(screen.getAllByText(/PDT|PST/).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/CDT|CST/).length).toBeGreaterThan(0);
    });

    it("switches both legs to UTC when that mode is selected", async () => {
      render(<StatusTimelineCard status={baseStatus} />);
      const select = screen.getByLabelText(/Show times in/);
      const { fireEvent } = await import("@testing-library/react");
      fireEvent.change(select, { target: { value: "utc" } });
      expect(screen.getAllByText(/UTC/).length).toBeGreaterThan(0);
    });
  });

  describe("diverted flight (SC-A4)", () => {
    const divertedStatus: FlightStatusResponse = {
      ...baseStatus,
      status: "diverted",
      diverted: {
        airport: {
          code: "KCRW",
          iata: "CRW",
          name: "West Virginia Intl Yeager",
          city: "Charleston",
          timezone: "America/New_York",
          gate: "D4",
          terminal: null,
        },
        scheduled_arrival: null,
        estimated_arrival: null,
        actual_arrival: "2026-09-13T01:31:45Z",
      },
    };

    it("renders a third column for the diverted-to destination", () => {
      render(<StatusTimelineCard status={divertedStatus} />);
      expect(screen.getByText("CRW")).toBeInTheDocument();
    });

    it("keeps the original destination visible", () => {
      render(<StatusTimelineCard status={divertedStatus} />);
      expect(screen.getByText("ORD")).toBeInTheDocument();
    });

    it("visually de-emphasizes the original destination column", () => {
      render(<StatusTimelineCard status={divertedStatus} />);
      expect(screen.getByLabelText("Original destination")).toHaveClass("leg--muted");
    });

    it("does not render a third column when there is no diverted status flight is diverted but data is missing", () => {
      render(<StatusTimelineCard status={{ ...divertedStatus, diverted: null }} />);
      expect(screen.queryByLabelText("Diverted to")).not.toBeInTheDocument();
    });
  });

  describe("airport city/country location line", () => {
    it("shows city and country together when both are known", () => {
      render(
        <StatusTimelineCard status={baseStatus} originCountry="US" destinationCountry="US" />,
      );
      expect(screen.getByText("San Francisco, US")).toBeInTheDocument();
      expect(screen.getByText("Chicago, US")).toBeInTheDocument();
    });

    it("falls back to just the city when country isn't known yet", () => {
      render(<StatusTimelineCard status={baseStatus} />);
      expect(screen.getByText("San Francisco")).toBeInTheDocument();
      expect(screen.getByText("Chicago")).toBeInTheDocument();
    });

    it("renders nothing for the location line when neither city nor country is known", () => {
      const status: FlightStatusResponse = {
        ...baseStatus,
        origin: { ...baseStatus.origin, city: null },
      };
      render(<StatusTimelineCard status={status} />);
      expect(screen.queryByText(/^,|,$/)).not.toBeInTheDocument();
    });
  });

  describe("map links (SC-E3)", () => {
    it("provides a maps link for each airport with a name", () => {
      render(<StatusTimelineCard status={baseStatus} />);
      const links = screen.getAllByRole("link", { name: /View on map/ });
      expect(links.length).toBe(2);
      expect(links[0]).toHaveAttribute(
        "href",
        expect.stringContaining(encodeURIComponent("San Francisco International Airport")),
      );
    });

    it("includes the terminal in the maps query when known", () => {
      render(<StatusTimelineCard status={baseStatus} />);
      const links = screen.getAllByRole("link", { name: /View on map/ });
      // destination has terminal "1"
      expect(links[1]).toHaveAttribute("href", expect.stringContaining(encodeURIComponent("Terminal 1")));
    });
  });
});
