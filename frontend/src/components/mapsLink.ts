/**
 * Builds a maps search URL for an airport (and terminal, when known) — see
 * docs/features/status-card-requirements.md#SC-E3. No terminal-level geocoordinates are available from
 * any source in use, so this is deliberately a TEXT-BASED search query (works with Google Maps and
 * Apple Maps' web fallback), not a precise pin — good enough for "get me there."
 */

export function airportMapsUrl(
  airportName: string | null,
  city: string | null,
  terminal: string | null,
): string {
  const place = airportName ?? city ?? "airport";
  const query = terminal ? `Terminal ${terminal}, ${place}` : place;
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}`;
}
