import { TIMEZONE_MODE_LABELS, type TimezoneMode } from "./statusCardTime";

interface Props {
  mode: TimezoneMode;
  onChange: (mode: TimezoneMode) => void;
}

const MODES: TimezoneMode[] = ["per_leg", "origin", "destination", "utc"];

/** SC-B2: lets the viewer override the default per-leg-local time display to a single uniform
 * timezone for the whole card. */
export function TimezoneModeSelect({ mode, onChange }: Props) {
  return (
    <label className="timezone-select">
      <span className="timezone-select__label">Show times in:</span>
      <select value={mode} onChange={(e) => onChange(e.target.value as TimezoneMode)}>
        {MODES.map((m) => (
          <option key={m} value={m}>
            {TIMEZONE_MODE_LABELS[m]}
          </option>
        ))}
      </select>
    </label>
  );
}
