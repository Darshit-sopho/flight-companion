import { renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../src/api/client", () => ({
  api: { getFlightStatus: vi.fn() },
}));

import { api } from "../../src/api/client";
import { useFlightStatus } from "../../src/hooks/useFlightStatus";

describe("useFlightStatus", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    Object.defineProperty(document, "visibilityState", { value: "visible", configurable: true });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.mocked(api.getFlightStatus).mockReset();
  });

  it("stops polling once the flight has landed", async () => {
    vi.mocked(api.getFlightStatus).mockResolvedValue({ status: "landed" } as never);

    renderHook(() => useFlightStatus("UAL123-2026-09-12"));

    await vi.waitFor(() => expect(api.getFlightStatus).toHaveBeenCalledTimes(1));
    await vi.advanceTimersByTimeAsync(60_000);

    expect(api.getFlightStatus).toHaveBeenCalledTimes(1);
  });

  it("keeps polling while the flight is still active", async () => {
    vi.mocked(api.getFlightStatus).mockResolvedValue({ status: "active" } as never);

    renderHook(() => useFlightStatus("UAL123-2026-09-12"));

    await vi.waitFor(() => expect(api.getFlightStatus).toHaveBeenCalledTimes(1));
    await vi.advanceTimersByTimeAsync(30_000);

    expect(api.getFlightStatus).toHaveBeenCalledTimes(2);
  });
});
