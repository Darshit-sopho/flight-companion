import type { AirportResponse } from "../api/client";

interface Props {
  label: string;
  airport: AirportResponse | null;
  loading: boolean;
}

export function AirportInfoPanel({ label, airport, loading }: Props) {
  return (
    <div className="card airport-card" aria-label={`${label} airport info`}>
      <h3>{label}</h3>
      {loading && <p>Loading…</p>}
      {!loading && !airport && <p>Airport info unavailable.</p>}
      {!loading && airport && (
        <>
          <p className="airport-card__name">{airport.name ?? airport.code}</p>
          <p>
            {airport.city ?? "—"} · {airport.code}
          </p>
          {airport.local_time && (
            <p className="airport-card__time">
              Local time:{" "}
              {new Date(airport.local_time).toLocaleTimeString(undefined, {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </p>
          )}
        </>
      )}
    </div>
  );
}
