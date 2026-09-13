/**
 * The only module allowed to call the backend (see CONTRIBUTING.md). Types here mirror the Pydantic
 * schemas in backend/app/schemas/flight.py — keep both in sync, along with docs/API.md, when either
 * changes.
 */

export type FlightStatusValue = "scheduled" | "active" | "landed" | "cancelled" | "diverted";
export type TrackState = "tracking" | "not_airborne" | "landed" | "unavailable";
export type Trend = "improving" | "worsening" | "stable";

export interface FlightSearchResponse {
  flight_id: string;
  ident: string;
  origin: string | null;
  destination: string | null;
  scheduled_departure: string | null;
}

export interface AirportRef {
  code: string | null;
  /** IATA code (e.g. "SFO") — the identity travelers actually recognize; `code` is ICAO (e.g. "KSFO"). */
  iata: string | null;
  name: string | null;
  city: string | null;
  timezone: string | null;
  gate: string | null;
  terminal: string | null;
}

export interface AircraftRef {
  registration: string | null;
  type: string | null;
}

export interface OperatorRef {
  icao: string | null;
  iata: string | null;
  /** Best-effort friendly name from a small static lookup; null if the code isn't in that table. */
  name: string | null;
}

export interface DivertedInfo {
  /** The ACTUAL landing airport — distinct from FlightStatusResponse.destination, which stays the
   * originally-filed destination so the UI can show both. */
  airport: AirportRef;
  scheduled_arrival: string | null;
  estimated_arrival: string | null;
  actual_arrival: string | null;
}

export interface FlightStatusResponse {
  flight_id: string;
  ident: string;
  status: FlightStatusValue;
  origin: AirportRef;
  destination: AirportRef;
  scheduled_departure: string | null;
  estimated_departure: string | null;
  actual_departure: string | null;
  scheduled_arrival: string | null;
  estimated_arrival: string | null;
  actual_arrival: string | null;
  delay_minutes: number | null;
  aircraft: AircraftRef;
  operator: OperatorRef | null;
  progress_percent: number | null;
  flight_duration_minutes: number | null;
  route_distance: number | null;
  /** Non-null only when status === "diverted". */
  diverted: DivertedInfo | null;
}

export interface HistoryOccurrence {
  date: string | null;
  delay_minutes: number | null;
  on_time: boolean | null;
}

export interface FlightHistoryResponse {
  flight_id: string;
  on_time_percentage: number | null;
  average_delay_minutes: number | null;
  trend: Trend;
  occurrences: HistoryOccurrence[];
}

export interface Position {
  lat: number;
  lon: number;
  altitude_ft: number | null;
  ground_speed_kt: number | null;
  heading_deg: number | null;
  on_ground: boolean;
  recorded_at: string;
}

export interface Resolution {
  method: string | null;
  confidence: string | null;
}

export interface TrackResponse {
  state: TrackState;
  position: Position | null;
  resolution: Resolution | null;
}

export interface AirportResponse {
  code: string;
  name: string | null;
  city: string | null;
  country: string | null;
  timezone: string | null;
  local_time: string | null;
}

export type WeatherBucket =
  | "clear"
  | "partly_cloudy"
  | "overcast"
  | "fog"
  | "rain"
  | "snow"
  | "thunderstorm";

export interface WeatherReading {
  bucket: WeatherBucket | null;
  temp_f: number | null;
  at: string;
}

export interface AirportWeatherResponse {
  code: string;
  now: WeatherReading;
  /** Null when no cached forecast hour falls within ~3h of the requested time. */
  outlook: WeatherReading | null;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string): Promise<T> {
  const response = await fetch(path);
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new ApiError(response.status, body.detail ?? response.statusText);
  }
  return response.json() as Promise<T>;
}

async function requestBlob(path: string): Promise<Blob> {
  const response = await fetch(path);
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new ApiError(response.status, body.detail ?? response.statusText);
  }
  return response.blob();
}

export const api = {
  searchFlight(ident: string, date: string): Promise<FlightSearchResponse> {
    const params = new URLSearchParams({ ident, date });
    return request(`/api/flights/search?${params.toString()}`);
  },
  getFlightStatus(flightId: string): Promise<FlightStatusResponse> {
    return request(`/api/flights/${encodeURIComponent(flightId)}`);
  },
  getFlightHistory(flightId: string, limit = 10): Promise<FlightHistoryResponse> {
    return request(`/api/flights/${encodeURIComponent(flightId)}/history?limit=${limit}`);
  },
  getFlightTrack(flightId: string): Promise<TrackResponse> {
    return request(`/api/flights/${encodeURIComponent(flightId)}/track`);
  },
  getAirport(code: string): Promise<AirportResponse> {
    return request(`/api/airports/${encodeURIComponent(code)}`);
  },
  getAirportWeather(code: string, at?: string): Promise<AirportWeatherResponse> {
    const query = at ? `?at=${encodeURIComponent(at)}` : "";
    return request(`/api/airports/${encodeURIComponent(code)}/weather${query}`);
  },
  getFlightCardImageBlob(flightId: string): Promise<Blob> {
    return requestBlob(`/api/flights/${encodeURIComponent(flightId)}/card.png`);
  },
};
