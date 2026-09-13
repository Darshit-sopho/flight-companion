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
    let hasFetchedOnce = false;

    const tick = async () => {
      if (cancelled || stoppedRef.current) return;
      // Only the RECURRING poll is skipped while hidden — the very first fetch always goes through
      // regardless of visibility, or a link opened in a background tab (common when tapping a link
      // from a messaging app) would show a loading state forever until the tab is focused.
      if (hasFetchedOnce && document.visibilityState === "hidden") {
        timer = setTimeout(tick, intervalMs);
        return;
      }
      try {
        const result = await fetcher();
        hasFetchedOnce = true;
        if (cancelled) return;
        setData(result);
        setError(null);
        if (shouldStop(result)) {
          stoppedRef.current = true;
          return;
        }
      } catch (err) {
        hasFetchedOnce = true;
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
