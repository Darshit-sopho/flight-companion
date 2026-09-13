import type { FlightStatusValue } from "../api/client";

interface Props {
  progressPercent: number | null;
  status: FlightStatusValue;
}

/** SC-A1: a flight-progress indicator between the origin/destination legs, driven by AeroAPI's
 * progress_percent. Forced to 0/100 for scheduled/landed regardless of what AeroAPI reports (SC-A1.1/
 * A1.2), since those are unambiguous regardless of data quirks. Hidden entirely for cancelled flights
 * (nothing to show progress toward); shown for diverted flights using whatever percent is available,
 * since the 3-column layout already communicates the diversion itself.
 */
export function FlightProgressBar({ progressPercent, status }: Props) {
  if (status === "cancelled") return null;

  const percent =
    status === "scheduled" ? 0 : status === "landed" ? 100 : (progressPercent ?? 0);
  const clamped = Math.max(0, Math.min(100, percent));

  return (
    <div
      className="flight-progress"
      role="progressbar"
      aria-valuenow={clamped}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label="Flight progress"
    >
      <div className="flight-progress__track">
        <div className="flight-progress__fill" style={{ width: `${clamped}%` }} />
      </div>
    </div>
  );
}
