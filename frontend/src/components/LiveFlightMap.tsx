import "leaflet/dist/leaflet.css";

import { useEffect } from "react";
import { MapContainer, Marker, Polyline, TileLayer, useMap } from "react-leaflet";

import type { Position, TrackResponse } from "../api/client";
import { planeIcon } from "./planeIcon";

interface Props {
  track: TrackResponse | null;
  trail: Position[];
}

function Recenter({ lat, lon }: { lat: number; lon: number }) {
  const map = useMap();
  useEffect(() => {
    map.setView([lat, lon], map.getZoom(), { animate: true });
  }, [lat, lon, map]);
  return null;
}

function Placeholder({ message }: { message: string }) {
  return (
    <section className="card map-card" aria-label="Live map">
      <h2>Live map</h2>
      <div className="map-placeholder">{message}</div>
    </section>
  );
}

export function LiveFlightMap({ track, trail }: Props) {
  if (!track || track.state === "not_airborne") {
    return <Placeholder message="Not airborne yet — live tracking will start at departure." />;
  }
  if (track.state === "landed") {
    return <Placeholder message="This flight has landed. Live tracking has ended." />;
  }
  if (track.state === "unavailable" || !track.position) {
    return <Placeholder message="Live tracking is unavailable for this aircraft right now." />;
  }

  const { lat, lon, heading_deg, altitude_ft, ground_speed_kt, on_ground } = track.position;
  const trailPositions: [number, number][] = trail.map((p) => [p.lat, p.lon]);

  return (
    <section className="card map-card" aria-label="Live map">
      <h2>Live map</h2>
      <div className="map-container">
        <MapContainer
          center={[lat, lon]}
          zoom={7}
          scrollWheelZoom
          style={{ height: "320px", width: "100%" }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {trailPositions.length > 1 && <Polyline positions={trailPositions} color="#4f7cff" />}
          <Marker position={[lat, lon]} icon={planeIcon(heading_deg)} />
          <Recenter lat={lat} lon={lon} />
        </MapContainer>
      </div>
      <dl className="map-stats">
        <div>
          <dt>Altitude</dt>
          <dd>
            {on_ground
              ? "On ground"
              : altitude_ft
                ? `${Math.round(altitude_ft).toLocaleString()} ft`
                : "—"}
          </dd>
        </div>
        <div>
          <dt>Speed</dt>
          <dd>{ground_speed_kt ? `${Math.round(ground_speed_kt)} kt` : "—"}</dd>
        </div>
        <div>
          <dt>Heading</dt>
          <dd>{heading_deg !== null ? `${Math.round(heading_deg)}°` : "—"}</dd>
        </div>
      </dl>
    </section>
  );
}
