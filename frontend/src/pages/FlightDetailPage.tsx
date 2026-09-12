import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import {
  api,
  ApiError,
  type AirportResponse,
  type FlightHistoryResponse,
  type Position,
} from "../api/client";
import { AirportInfoPanel } from "../components/AirportInfoPanel";
import { DelayTrendChart } from "../components/DelayTrendChart";
import { LiveFlightMap } from "../components/LiveFlightMap";
import { ShareLinkButton } from "../components/ShareLinkButton";
import { StatusTimelineCard } from "../components/StatusTimelineCard";
import { useFlightStatus } from "../hooks/useFlightStatus";
import { useLiveTrack } from "../hooks/useLiveTrack";

const MAX_TRAIL_LENGTH = 50;

function FlightDetailContent({ flightId }: { flightId: string }) {
  const { data: status, error: statusError } = useFlightStatus(flightId);
  const { data: track } = useLiveTrack(flightId);
  const [history, setHistory] = useState<FlightHistoryResponse | null>(null);
  const [trail, setTrail] = useState<Position[]>([]);
  const [origin, setOrigin] = useState<AirportResponse | null>(null);
  const [destination, setDestination] = useState<AirportResponse | null>(null);

  useEffect(() => {
    api
      .getFlightHistory(flightId)
      .then(setHistory)
      .catch(() => setHistory(null));
  }, [flightId]);

  useEffect(() => {
    if (!status?.origin.code) return;
    api
      .getAirport(status.origin.code)
      .then(setOrigin)
      .catch(() => setOrigin(null));
  }, [status?.origin.code]);

  useEffect(() => {
    if (!status?.destination.code) return;
    api
      .getAirport(status.destination.code)
      .then(setDestination)
      .catch(() => setDestination(null));
  }, [status?.destination.code]);

  useEffect(() => {
    if (track?.state === "tracking" && track.position) {
      const position = track.position;
      setTrail((prev) => [...prev.slice(-(MAX_TRAIL_LENGTH - 1)), position]);
    }
  }, [track]);

  if (statusError) {
    return (
      <p role="alert" className="error-text">
        Couldn't load this flight: {statusError.message}
      </p>
    );
  }
  if (!status) {
    return <p>Loading flight…</p>;
  }

  return (
    <>
      <StatusTimelineCard status={status} />
      <LiveFlightMap track={track} trail={trail} />
      {history && <DelayTrendChart history={history} />}
      <div className="airport-panels">
        <AirportInfoPanel
          label={`Departure — ${status.origin.code ?? ""}`}
          airport={origin}
          loading={!origin && !!status.origin.code}
        />
        <AirportInfoPanel
          label={`Arrival — ${status.destination.code ?? ""}`}
          airport={destination}
          loading={!destination && !!status.destination.code}
        />
      </div>
      <ShareLinkButton />
    </>
  );
}

export function FlightDetailPage() {
  const { ident = "", date = "" } = useParams();
  const [flightId, setFlightId] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  useEffect(() => {
    setFlightId(null);
    setNotFound(false);
    setSearchError(null);
    api
      .searchFlight(ident, date)
      .then((result) => setFlightId(result.flight_id))
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 404) {
          setNotFound(true);
        } else {
          // A non-404 failure (backend error, network issue, etc.) is not the same as "no such
          // flight" — surface it distinctly so it isn't mistaken for a bad flight number/date.
          setSearchError(err instanceof Error ? err.message : "Something went wrong.");
        }
      });
  }, [ident, date]);

  return (
    <main className="page detail-page">
      <h1>
        {ident} · {date}
      </h1>
      {notFound && (
        <p role="alert">
          No flight found for {ident} on {date}. Double-check the flight number and date.
        </p>
      )}
      {searchError && (
        <p role="alert" className="error-text">
          Couldn't look up this flight: {searchError}
        </p>
      )}
      {!notFound && !searchError && flightId && <FlightDetailContent flightId={flightId} />}
      {!notFound && !searchError && !flightId && <p>Looking up flight…</p>}
    </main>
  );
}
