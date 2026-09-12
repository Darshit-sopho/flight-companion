import { useEffect, useRef, useState } from "react";

/**
 * Generic polling primitive shared by useFlightStatus and useLiveTrack. Pauses while the tab is hidden
 * (Page Visibility API) and stops entirely once `shouldStop(data)` returns true — see
 * docs/ARCHITECTURE.md#live-map-update-strategy for why this matters (don't keep polling OpenSky/AeroAPI
 * for a page nobody's looking at, or a flight that's already landed).
 */
export function usePolling<T>(
  fetcher: () => Promise<T>,
  intervalMs: number,
  shouldStop: (data: T) => boolean,
) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const stoppedRef = useRef(false);

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    stoppedRef.current = false;

    const tick = async () => {
      if (cancelled || stoppedRef.current) return;
      if (document.visibilityState === "hidden") {
        timer = setTimeout(tick, intervalMs);
        return;
      }
      try {
        const result = await fetcher();
        if (cancelled) return;
        setData(result);
        setError(null);
        if (shouldStop(result)) {
          stoppedRef.current = true;
          return;
        }
      } catch (err) {
        if (!cancelled) setError(err as Error);
      }
      if (!cancelled && !stoppedRef.current) {
        timer = setTimeout(tick, intervalMs);
      }
    };

    void tick();

    const onVisibilityChange = () => {
      if (document.visibilityState === "visible" && !stoppedRef.current) {
        if (timer) clearTimeout(timer);
        void tick();
      }
    };
    document.addEventListener("visibilitychange", onVisibilityChange);

    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
    // Callers must memoize `fetcher` (e.g. useCallback keyed on flightId) so this effect only restarts
    // when what's being polled actually changes, not on every render.
  }, [fetcher, intervalMs, shouldStop]);

  return { data, error };
}
