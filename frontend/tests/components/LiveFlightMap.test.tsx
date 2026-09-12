import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

// react-leaflet needs real browser layout APIs that jsdom doesn't fully provide — mocked here so these
// tests focus on FR4.3/FR4.4 (distinct track states), not Leaflet's internals.
vi.mock("react-leaflet", () => ({
  MapContainer: ({ children }: { children: ReactNode }) => <div data-testid="map">{children}</div>,
  TileLayer: () => null,
  Marker: () => <div data-testid="marker" />,
  Polyline: () => null,
  useMap: () => ({ setView: vi.fn(), getZoom: () => 7 }),
}));

import type { TrackResponse } from "../../src/api/client";
import { LiveFlightMap } from "../../src/components/LiveFlightMap";
import { planeIcon } from "../../src/components/planeIcon";

const trackingResponse: TrackResponse = {
  state: "tracking",
  position: {
    lat: 41.9,
    lon: -87.9,
    altitude_ft: 34000,
    ground_speed_kt: 480,
    heading_deg: 92,
    on_ground: false,
    recorded_at: "2026-09-12T15:00:00Z",
  },
  resolution: { method: "registration_lookup", confidence: "high" },
};

describe("LiveFlightMap", () => {
  it("shows a distinct message when not airborne yet", () => {
    render(<LiveFlightMap track={{ state: "not_airborne", position: null, resolution: null }} trail={[]} />);
    expect(screen.getByText(/Not airborne yet/)).toBeInTheDocument();
  });

  it("treats a null track (still loading) the same as not airborne", () => {
    render(<LiveFlightMap track={null} trail={[]} />);
    expect(screen.getByText(/Not airborne yet/)).toBeInTheDocument();
  });

  it("shows a distinct message when landed", () => {
    render(<LiveFlightMap track={{ state: "landed", position: null, resolution: null }} trail={[]} />);
    expect(screen.getByText(/has landed/)).toBeInTheDocument();
  });

  it("shows a distinct message when tracking is unavailable, never a blank map", () => {
    render(<LiveFlightMap track={{ state: "unavailable", position: null, resolution: null }} trail={[]} />);
    expect(screen.getByText(/unavailable/)).toBeInTheDocument();
    expect(screen.queryByTestId("map")).not.toBeInTheDocument();
  });

  it("renders the map with a marker and position stats when tracking", () => {
    render(<LiveFlightMap track={trackingResponse} trail={[]} />);
    expect(screen.getByTestId("map")).toBeInTheDocument();
    expect(screen.getByTestId("marker")).toBeInTheDocument();
    expect(screen.getByText(/34,000 ft/)).toBeInTheDocument();
    expect(screen.getByText(/480 kt/)).toBeInTheDocument();
  });

  it("shows 'on ground' instead of a stale altitude when on_ground is true", () => {
    const onGround: TrackResponse = {
      ...trackingResponse,
      position: { ...trackingResponse.position!, on_ground: true, altitude_ft: 0 },
    };
    render(<LiveFlightMap track={onGround} trail={[]} />);
    expect(screen.getByText("On ground")).toBeInTheDocument();
  });
});

describe("planeIcon", () => {
  // Regression test: an emoji-based icon rotated fine in the DOM but looked visually wrong because
  // its default artwork orientation isn't guaranteed to point north — a plain CSS-rotation check
  // alone wouldn't have caught that class of bug, but this at least locks in the rotation math on the
  // SVG icon that replaced it (nose-up at 0deg, clockwise from there — same convention as OpenSky's
  // true_track).
  it("rotates the icon by the given heading, clockwise from north", () => {
    const icon = planeIcon(92);
    expect(icon.options.html).toContain("rotate(92deg)");
  });

  it("defaults to no rotation when heading is unknown", () => {
    const icon = planeIcon(null);
    expect(icon.options.html).toContain("rotate(0deg)");
  });
});
