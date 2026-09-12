import { renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../src/api/client", () => ({
  api: { getFlightTrack: vi.fn() },
}));

import { api } from "../../src/api/client";
import { useLiveTrack } from "../../src/hooks/useLiveTrack";

describe("useLiveTrack", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    Object.defineProperty(document, "visibilityState", { value: "visible", configurable: true });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.mocked(api.getFlightTrack).mockReset();
  });

  it("stops polling once the flight has landed", async () => {
    vi.mocked(api.getFlightTrack).mockResolvedValue({
      state: "landed",
      position: null,
      resolution: null,
    } as never);

    renderHook(() => useLiveTrack("UAL123-2026-09-12"));

    await vi.waitFor(() => expect(api.getFlightTrack).toHaveBeenCalledTimes(1));
    await vi.advanceTimersByTimeAsync(60_000);

    expect(api.getFlightTrack).toHaveBeenCalledTimes(1);
  });

  it("keeps polling while tracking is merely unavailable (not yet a terminal state)", async () => {
    vi.mocked(api.getFlightTrack).mockResolvedValue({
      state: "unavailable",
      position: null,
      resolution: null,
    } as never);

    renderHook(() => useLiveTrack("UAL123-2026-09-12"));

    await vi.waitFor(() => expect(api.getFlightTrack).toHaveBeenCalledTimes(1));
    await vi.advanceTimersByTimeAsync(12_000);

    expect(api.getFlightTrack).toHaveBeenCalledTimes(2);
  });
});
