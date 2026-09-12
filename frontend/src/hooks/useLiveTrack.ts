import { useCallback } from "react";

import { api, type TrackResponse } from "../api/client";
import { usePolling } from "./usePolling";

// Matches OPENSKY_MIN_POLL_INTERVAL_SECONDS' order of magnitude on the backend — see
// docs/ARCHITECTURE.md#live-map-update-strategy. The backend throttles its own upstream OpenSky calls
// independent of this, so polling a little faster than strictly needed here is harmless.
const POLL_INTERVAL_MS = 12_000;

/** Polls a flight's live position; stops only once the flight has definitively landed/ended. */
export function useLiveTrack(flightId: string) {
  const fetcher = useCallback(() => api.getFlightTrack(flightId), [flightId]);
  const shouldStop = useCallback((data: TrackResponse) => data.state === "landed", []);
  return usePolling(fetcher, POLL_INTERVAL_MS, shouldStop);
}
