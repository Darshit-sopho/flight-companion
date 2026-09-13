/**
 * Compact weather glyph icons (SC-D2), bucketed from Open-Meteo's WMO weather codes on the backend
 * (see backend/app/services/wmo_weather_codes.py) into 7 icons. Plain inline SVG, same convention as
 * statusCardIcons.tsx -- no icon library dependency.
 */

interface IconProps {
  className?: string;
}

const BASE_PROPS = {
  width: 14,
  height: 14,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  "aria-hidden": true,
};

const _CLOUD = "M6 18a4 4 0 0 1-.5-7.97A5 5 0 0 1 15 8a4.5 4.5 0 0 1 1 8.9";

export function ClearIcon({ className }: IconProps) {
  return (
    <svg {...BASE_PROPS} className={className}>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 3v2M12 19v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M3 12h2M19 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4" />
    </svg>
  );
}

export function PartlyCloudyIcon({ className }: IconProps) {
  return (
    <svg {...BASE_PROPS} className={className}>
      <circle cx="8" cy="7" r="3" />
      <path d="M10 14a4 4 0 0 1-.5-7.96" />
      <path d="M9.5 14h8a3.5 3.5 0 0 0 .5-6.96 4.5 4.5 0 0 0-8.62-1.4" />
    </svg>
  );
}

export function OvercastIcon({ className }: IconProps) {
  return (
    <svg {...BASE_PROPS} className={className}>
      <path d={_CLOUD} />
      <path d="M4 21h13" />
    </svg>
  );
}

export function FogIcon({ className }: IconProps) {
  return (
    <svg {...BASE_PROPS} className={className}>
      <path d="M6 16a4 4 0 0 1-.5-7.97A5 5 0 0 1 15 6a4.5 4.5 0 0 1 1 8.9" />
      <path d="M3 18h18M5 21h14" />
    </svg>
  );
}

export function RainIcon({ className }: IconProps) {
  return (
    <svg {...BASE_PROPS} className={className}>
      <path d={_CLOUD} />
      <path d="M8 19l-1 2M12 19l-1 2M16 19l-1 2" />
    </svg>
  );
}

export function SnowIcon({ className }: IconProps) {
  return (
    <svg {...BASE_PROPS} className={className}>
      <path d={_CLOUD} />
      <path d="M8 19v3M6.5 20.5h3M12 19v3M10.5 20.5h3M16 19v3M14.5 20.5h3" />
    </svg>
  );
}

export function ThunderstormIcon({ className }: IconProps) {
  return (
    <svg {...BASE_PROPS} className={className}>
      <path d={_CLOUD} />
      <path d="M13 15l-3 5h3l-2 4" />
    </svg>
  );
}
