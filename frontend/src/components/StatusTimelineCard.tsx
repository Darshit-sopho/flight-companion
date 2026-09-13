import { useEffect, useState } from "react";

import type { AirportRef, FlightStatusResponse } from "../api/client";
import { FlightProgressBar } from "./FlightProgressBar";
import { airportMapsUrl } from "./mapsLink";
import { countdownLabel, formatDistance, formatDurationMinutes } from "./statusCardFormat";
import { DelayIcon, DurationIcon, GateIcon, MapPinIcon, OperatorIcon, TerminalIcon } from "./statusCardIcons";
import { formatTimeInZone, resolveTimezone, zoneAbbreviation, type TimezoneMode } from "./statusCardTime";
import { TimezoneModeSelect } from "./TimezoneModeSelect";

interface Props {
  status: FlightStatusResponse;
  originCountry?: string | null;
  destinationCountry?: string | null;
}

const STATUS_LABEL: Record<FlightStatusResponse["status"], string> = {
  scheduled: "Scheduled",
  active: "In the air",
  landed: "Landed",
  cancelled: "Cancelled",
  diverted: "Diverted",
};

function delayLabel(delayMinutes: number | null): { text: string; tone: "ok" | "warn" | "bad" } {
  if (delayMinutes === null) return { text: "No delay data yet", tone: "ok" };
  if (delayMinutes <= 15) return { text: `On time (${delayMinutes}m)`, tone: "ok" };
  if (delayMinutes <= 45) return { text: `Delayed ${delayMinutes}m`, tone: "warn" };
  return { text: `Delayed ${delayMinutes}m`, tone: "bad" };
}

function TimeCell({ iso, tz }: { iso: string | null; tz: string | undefined }) {
  if (!iso) return <>not yet available</>;
  const abbr = zoneAbbreviation(iso, tz);
  return (
    <>
      {formatTimeInZone(iso, tz)}
      {abbr && <span className="tz-label"> {abbr}</span>}
    </>
  );
}

interface LegColumnProps {
  label: string;
  airport: AirportRef;
  scheduled: string | null;
  estimated: string | null;
  actual: string | null;
  isCancelled: boolean;
  tz: string | undefined;
  muted?: boolean;
  country?: string | null;
}

function LegColumn({
  label,
  airport,
  scheduled,
  estimated,
  actual,
  isCancelled,
  tz,
  muted,
  country,
}: LegColumnProps) {
  const location = [airport.city, country].filter(Boolean).join(", ");
  return (
    <div className={`leg${muted ? " leg--muted" : ""}`} aria-label={label}>
      <h3>{airport.iata ?? airport.code ?? "—"}</h3>
      {(airport.name ?? airport.city) && (
        <p className="leg__name">({airport.name ?? airport.city})</p>
      )}
      {location && <p className="leg__location">{location}</p>}
      <dl>
        <div>
          <dt>Scheduled</dt>
          <dd>
            <TimeCell iso={scheduled} tz={tz} />
          </dd>
        </div>
        <div>
          <dt>{isCancelled ? "Status" : actual ? "Actual" : "Estimated"}</dt>
          <dd>{isCancelled ? "Cancelled" : <TimeCell iso={actual ?? estimated} tz={tz} />}</dd>
        </div>
        <div>
          <dt>
            <GateIcon /> Gate / <TerminalIcon /> Terminal
          </dt>
          <dd>
            {airport.gate ?? "not yet available"} / {airport.terminal ?? "—"}
          </dd>
        </div>
      </dl>
      {(airport.name ?? airport.city) && (
        <a
          className="leg__maps-link"
          href={airportMapsUrl(airport.name, airport.city, airport.terminal)}
          target="_blank"
          rel="noreferrer"
        >
          <MapPinIcon /> View on map
        </a>
      )}
      {airport.code && (
        <p className="leg__codes">
          {airport.iata ?? "—"} · {airport.code}
        </p>
      )}
    </div>
  );
}

export function StatusTimelineCard({ status, originCountry, destinationCountry }: Props) {
  const delay = delayLabel(status.delay_minutes);
  const [timezoneMode, setTimezoneMode] = useState<TimezoneMode>("per_leg");
  const [nowMs, setNowMs] = useState(() => Date.now());

  // SC-D1: a live, client-side-ticking countdown between polls — 30s is frequent enough to keep an
  // "in Xh Ym" label feeling current without re-rendering on every second.
  useEffect(() => {
    const interval = setInterval(() => setNowMs(Date.now()), 30_000);
    return () => clearInterval(interval);
  }, []);

  const isCancelled = status.status === "cancelled";
  const isDiverted = status.status === "diverted";

  const originTz = resolveTimezone(
    timezoneMode,
    status.origin.timezone,
    status.origin.timezone,
    status.destination.timezone,
  );
  const destinationTz = resolveTimezone(
    timezoneMode,
    status.destination.timezone,
    status.origin.timezone,
    status.destination.timezone,
  );

  const countdown =
    status.status === "scheduled"
      ? countdownLabel(status.estimated_departure ?? status.scheduled_departure, nowMs)
      : status.status === "active"
        ? countdownLabel(status.estimated_arrival ?? status.scheduled_arrival, nowMs)
        : null;
  const countdownText =
    status.status === "scheduled" ? `Departs in ${countdown}` : `Arrives in ${countdown}`;

  const duration = formatDurationMinutes(status.flight_duration_minutes);
  const distance = formatDistance(status.route_distance);

  return (
    <section className="card status-card" aria-label="Flight status">
      <div className="status-card__header">
        <h2>
          {status.ident} · {STATUS_LABEL[status.status]}
        </h2>
        <span className={`badge badge--${delay.tone}`}>
          <DelayIcon /> {delay.text}
        </span>
      </div>

      {status.operator && (
        <p className="status-card__operator">
          <OperatorIcon /> Operated by {status.operator.name ?? status.operator.icao ?? "—"}
          {status.operator.icao && ` (${status.operator.icao})`}
        </p>
      )}

      {(duration ?? distance ?? countdown) && (
        <p className="status-card__trip-info">
          {duration && (
            <span>
              <DurationIcon /> {duration}
            </span>
          )}
          {distance && <span>{distance}</span>}
          {countdown && <span className="status-card__countdown">{countdownText}</span>}
        </p>
      )}

      <TimezoneModeSelect mode={timezoneMode} onChange={setTimezoneMode} />

      <FlightProgressBar progressPercent={status.progress_percent} status={status.status} />

      <div className="status-card__legs">
        <LegColumn
          label="Origin"
          airport={status.origin}
          scheduled={status.scheduled_departure}
          estimated={status.estimated_departure}
          actual={status.actual_departure}
          isCancelled={isCancelled}
          tz={originTz}
          country={originCountry}
        />

        <div className="leg-arrow" aria-hidden="true">
          →
        </div>

        <LegColumn
          label={isDiverted ? "Original destination" : "Destination"}
          airport={status.destination}
          scheduled={status.scheduled_arrival}
          estimated={status.estimated_arrival}
          actual={status.actual_arrival}
          isCancelled={isCancelled}
          tz={destinationTz}
          muted={isDiverted}
          country={destinationCountry}
        />

        {isDiverted && status.diverted && (
          <>
            <div className="leg-arrow" aria-hidden="true">
              →
            </div>
            <LegColumn
              label="Diverted to"
              airport={status.diverted.airport}
              scheduled={status.diverted.scheduled_arrival}
              estimated={status.diverted.estimated_arrival}
              actual={status.diverted.actual_arrival}
              isCancelled={false}
              tz={resolveTimezone(
                timezoneMode,
                status.diverted.airport.timezone,
                status.origin.timezone,
                status.diverted.airport.timezone,
              )}
            />
          </>
        )}
      </div>

      {status.aircraft.registration && (
        <p className="status-card__aircraft">
          Aircraft: {status.aircraft.registration} ({status.aircraft.type ?? "unknown type"})
        </p>
      )}
    </section>
  );
}
