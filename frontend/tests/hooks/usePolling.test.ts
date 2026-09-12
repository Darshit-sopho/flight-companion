import { renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { usePolling } from "../../src/hooks/usePolling";

function setVisibility(state: DocumentVisibilityState) {
  Object.defineProperty(document, "visibilityState", { value: state, configurable: true });
}

describe("usePolling", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    setVisibility("visible");
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("polls repeatedly until shouldStop returns true", async () => {
    let call = 0;
    const fetcher = vi.fn(async () => {
      call += 1;
      return call;
    });
    // Must be a stable reference, same as real callers are required to memoize (see usePolling's
    // doc comment) — an inline arrow function here would get a new identity on every state-driven
    // re-render and restart the polling effect, double-counting calls.
    const shouldStop = (data: number) => data >= 3;

    renderHook(() => usePolling(fetcher, 1000, shouldStop));

    await vi.waitFor(() => expect(fetcher).toHaveBeenCalledTimes(1));
    await vi.advanceTimersByTimeAsync(1000);
    await vi.advanceTimersByTimeAsync(1000);
    await vi.advanceTimersByTimeAsync(1000);

    expect(fetcher).toHaveBeenCalledTimes(3);
  });

  it("does not fetch while the tab is hidden", async () => {
    setVisibility("hidden");
    const fetcher = vi.fn(async () => "data");
    const shouldStop = () => false;

    renderHook(() => usePolling(fetcher, 1000, shouldStop));
    await vi.advanceTimersByTimeAsync(5000);

    expect(fetcher).not.toHaveBeenCalled();
  });

  it("stops scheduling further polls once shouldStop returns true", async () => {
    const fetcher = vi.fn(async () => "landed");
    const shouldStop = () => true;

    renderHook(() => usePolling(fetcher, 1000, shouldStop));

    await vi.waitFor(() => expect(fetcher).toHaveBeenCalledTimes(1));
    await vi.advanceTimersByTimeAsync(10000);

    expect(fetcher).toHaveBeenCalledTimes(1);
  });
});
