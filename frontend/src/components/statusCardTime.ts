/**
 * Timezone display logic for the status card — see docs/features/status-card-requirements.md#SC-B1-B3.
 *
 * Four display modes:
 *  - "per_leg" (default): each leg's times in that leg's own airport's local timezone.
 *  - "origin": both legs' times shown in the origin airport's timezone.
 *  - "destination": both legs' times shown in the destination airport's timezone.
 *  - "utc": both legs' times shown in UTC.
 */

export type TimezoneMode = "per_leg" | "origin" | "destination" | "utc";

export const TIMEZONE_MODE_LABELS: Record<TimezoneMode, string> = {
  per_leg: "Local time (per airport)",
  origin: "Origin time",
  destination: "Destination time",
  utc: "UTC",
};

/** Resolve which IANA timezone to actually format a given leg's time in, for the active mode. */
export function resolveTimezone(
  mode: TimezoneMode,
  legTimezone: string | null,
  originTimezone: string | null,
  destinationTimezone: string | null,
): string | undefined {
  switch (mode) {
    case "origin":
      return originTimezone ?? undefined;
    case "destination":
      return destinationTimezone ?? undefined;
    case "utc":
      return "UTC";
    case "per_leg":
    default:
      return legTimezone ?? undefined;
  }
}

/** Format an ISO datetime string in a specific IANA timezone (or the runtime default if undefined). */
export function formatTimeInZone(value: string | null, timeZone: string | undefined): string {
  if (!value) return "not yet available";
  return new Date(value).toLocaleString(undefined, {
    weekday: "short",
    hour: "2-digit",
    minute: "2-digit",
    timeZone,
  });
}

/** A short zone label ("PDT", "UTC", "GMT+2", ...) for the given instant + timezone, so it's never
 * ambiguous which clock a displayed time is in (SC-B3). Falls back to the raw timezone name/offset if
 * Intl can't produce a short form for some reason. */
export function zoneAbbreviation(value: string | null, timeZone: string | undefined): string {
  if (!value || !timeZone) return "";
  try {
    const parts = new Intl.DateTimeFormat(undefined, { timeZone, timeZoneName: "short" }).formatToParts(
      new Date(value),
    );
    return parts.find((p) => p.type === "timeZoneName")?.value ?? timeZone;
  } catch {
    return timeZone;
  }
}
