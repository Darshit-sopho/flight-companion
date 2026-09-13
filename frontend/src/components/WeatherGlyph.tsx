import type { WeatherBucket } from "../api/client";
import {
  ClearIcon,
  FogIcon,
  OvercastIcon,
  PartlyCloudyIcon,
  RainIcon,
  SnowIcon,
  ThunderstormIcon,
} from "./weatherIcons";

interface Props {
  /** Visible, leg-specific label so it's clear what time this reading is for at a glance, not just on
   * hover -- e.g. "Now", "At departure", "At arrival". See StatusTimelineCard's LegColumn.
   */
  label: string;
  bucket: WeatherBucket | null;
  tempF: number | null;
}

const ICON_BY_BUCKET: Record<WeatherBucket, (props: { className?: string }) => JSX.Element> = {
  clear: ClearIcon,
  partly_cloudy: PartlyCloudyIcon,
  overcast: OvercastIcon,
  fog: FogIcon,
  rain: RainIcon,
  snow: SnowIcon,
  thunderstorm: ThunderstormIcon,
};

const CONDITION_LABEL: Record<WeatherBucket, string> = {
  clear: "clear",
  partly_cloudy: "partly cloudy",
  overcast: "overcast",
  fog: "foggy",
  rain: "rain",
  snow: "snow",
  thunderstorm: "thunderstorms",
};

/** One compact glyph (label + icon + temp) for the status card's per-leg weather row (SC-D2). Two of
 * these sit side by side per leg: "Now" (current airport conditions) and a leg-specific "At departure"/
 * "At arrival" (forecast for the hour nearest that leg's scheduled/estimated time) -- see
 * StatusTimelineCard's LegColumn. The label is shown as visible text, not just a hover tooltip, since a
 * bare icon+temp pair gives no clue which of the two it is.
 */
export function WeatherGlyph({ label, bucket, tempF }: Props) {
  if (bucket === null && tempF === null) return null;

  const Icon = bucket ? ICON_BY_BUCKET[bucket] : null;
  const condition = bucket ? CONDITION_LABEL[bucket] : "unknown conditions";
  const temp = tempF !== null ? `${Math.round(tempF)}°F` : null;
  const title = `${label}: ${condition}${temp ? `, ${temp}` : ""}`;

  return (
    <span className="weather-glyph" title={title} aria-label={title}>
      <span className="weather-glyph__label">{label}</span>
      {Icon && <Icon />}
      {temp && <span className="weather-glyph__temp">{temp}</span>}
    </span>
  );
}
