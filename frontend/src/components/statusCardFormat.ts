/** Duration/countdown formatting for the status card — SC-C2 (flight duration), SC-E1 (visible
 * placement), SC-D1 (live countdown).
 */

export function formatDurationMinutes(totalMinutes: number | null): string | null {
  if (totalMinutes === null || totalMinutes < 0) return null;
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  if (hours === 0) return `${minutes}m`;
  if (minutes === 0) return `${hours}h`;
  return `${hours}h ${minutes}m`;
}

export function formatDistance(miles: number | null): string | null {
  if (miles === null) return null;
  return `${miles.toLocaleString()} mi`;
}

/** Minutes remaining until an ISO timestamp, or null if the timestamp is missing/already past. */
export function minutesUntil(targetIso: string | null, nowMs: number): number | null {
  if (!targetIso) return null;
  const targetMs = new Date(targetIso).getTime();
  const diffMinutes = Math.round((targetMs - nowMs) / 60_000);
  return diffMinutes > 0 ? diffMinutes : null;
}

/** A short "in Xh Ym" countdown label, or null when there's nothing to count down to. */
export function countdownLabel(targetIso: string | null, nowMs: number): string | null {
  const minutes = minutesUntil(targetIso, nowMs);
  if (minutes === null) return null;
  return formatDurationMinutes(minutes);
}
