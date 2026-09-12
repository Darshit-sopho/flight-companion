import L from "leaflet";

// A plain emoji (✈️) doesn't work here: its default artwork orientation varies by OS/browser font
// (and on at least one real font, looks nearly identical at 0/90/180 degrees), so rotating it never
// reliably lines up with compass headings. This inline SVG (Google's Material Icons "flight" glyph,
// Apache-2.0) is drawn nose-up by design, so `rotate(headingDeg)` — clockwise from north, same
// convention OpenSky's `true_track` uses — lines up correctly on every platform.
const PLANE_SVG_PATH =
  "M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2.5 1.5V22l3.5-1 3.5 1v-1.5L13 19v-6.5l8 2.5z";

export function planeIcon(headingDeg: number | null): L.DivIcon {
  const rotation = headingDeg ?? 0;
  return L.divIcon({
    html: `
      <svg width="24" height="24" viewBox="0 0 24 24" style="transform: rotate(${rotation}deg);">
        <path d="${PLANE_SVG_PATH}" fill="#4f7cff" stroke="#0b1220" stroke-width="0.6" />
      </svg>
    `,
    className: "plane-icon",
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });
}
