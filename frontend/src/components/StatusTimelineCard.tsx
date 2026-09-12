import type { FlightStatusResponse } from "../api/client";

interface Props {
  status: FlightStatusResponse;
}

function formatTime(value: string | null): string {
  if (!value) return "not yet available";
  return new Date(value).toLocaleString(undefined, {
    weekday: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
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

export function StatusTimelineCard({ status }: Props) {
  const delay = delayLabel(status.delay_minutes);

  return (
    <section className="card status-card" aria-label="Flight status">
      <div className="status-card__header">
        <h2>
          {status.ident} · {STATUS_LABEL[status.status]}
        </h2>
        <span className={`badge badge--${delay.tone}`}>{delay.text}</span>
      </div>

      <div className="status-card__legs">
        <div className="leg">
          <h3>{status.origin.code ?? "—"}</h3>
          <dl>
            <div>
              <dt>Scheduled</dt>
              <dd>{formatTime(status.scheduled_departure)}</dd>
            </div>
            <div>
              <dt>Estimated</dt>
              <dd>{formatTime(status.estimated_departure)}</dd>
            </div>
            <div>
              <dt>Actual</dt>
              <dd>{formatTime(status.actual_departure)}</dd>
            </div>
            <div>
              <dt>Gate / Terminal</dt>
              <dd>
                {status.origin.gate ?? "not yet available"} / {status.origin.terminal ?? "—"}
              </dd>
            </div>
          </dl>
        </div>

        <div className="leg-arrow" aria-hidden="true">
          →
        </div>

        <div className="leg">
          <h3>{status.destination.code ?? "—"}</h3>
          <dl>
            <div>
              <dt>Scheduled</dt>
              <dd>{formatTime(status.scheduled_arrival)}</dd>
            </div>
            <div>
              <dt>Estimated</dt>
              <dd>{formatTime(status.estimated_arrival)}</dd>
            </div>
            <div>
              <dt>Actual</dt>
              <dd>{formatTime(status.actual_arrival)}</dd>
            </div>
            <div>
              <dt>Gate / Terminal</dt>
              <dd>
                {status.destination.gate ?? "not yet available"} / {status.destination.terminal ?? "—"}
              </dd>
            </div>
          </dl>
        </div>
      </div>

      {status.aircraft.registration && (
        <p className="status-card__aircraft">
          Aircraft: {status.aircraft.registration} ({status.aircraft.type ?? "unknown type"})
        </p>
      )}
    </section>
  );
}
