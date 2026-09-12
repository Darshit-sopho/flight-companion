import { useCallback } from "react";

import { api, type FlightStatusResponse } from "../api/client";
import { usePolling } from "./usePolling";

const POLL_INTERVAL_MS = 30_000;
const TERMINAL_STATUSES = new Set(["landed", "cancelled"]);

/** Polls a flight's status; stops once the flight has landed or been cancelled. */
export function useFlightStatus(flightId: string) {
  const fetcher = useCallback(() => api.getFlightStatus(flightId), [flightId]);
  const shouldStop = useCallback(
    (data: FlightStatusResponse) => TERMINAL_STATUSES.has(data.status),
    [],
  );
  return usePolling(fetcher, POLL_INTERVAL_MS, shouldStop);
}
