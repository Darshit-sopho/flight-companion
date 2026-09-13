import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../src/api/client", () => ({
  api: { getFlightCardImageBlob: vi.fn() },
}));

import { api } from "../../src/api/client";
import { ShareImageButton } from "../../src/components/ShareImageButton";

const FAKE_BLOB = new Blob(["fake-png-bytes"], { type: "image/png" });

describe("ShareImageButton", () => {
  beforeEach(() => {
    vi.mocked(api.getFlightCardImageBlob).mockResolvedValue(FAKE_BLOB);
  });

  afterEach(() => {
    vi.mocked(api.getFlightCardImageBlob).mockReset();
    // @ts-expect-error -- test-only cleanup of a property we stub per-test.
    delete navigator.canShare;
    // @ts-expect-error -- same.
    delete navigator.share;
  });

  it("uses the Web Share API with the fetched image when file sharing is supported", async () => {
    const canShare = vi.fn().mockReturnValue(true);
    const share = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { canShare, share });

    render(<ShareImageButton flightId="UAL123-2026-09-12" />);
    fireEvent.click(screen.getByRole("button", { name: /Share as image/ }));

    await vi.waitFor(() => expect(share).toHaveBeenCalledTimes(1));
    const call = share.mock.calls[0][0];
    expect(call.files).toHaveLength(1);
    expect(call.files[0].name).toBe("flight-UAL123-2026-09-12.png");
  });

  it("falls back to a browser download when file sharing isn't supported", async () => {
    // No navigator.canShare/share at all -- e.g. a typical desktop browser.
    const createObjectURL = vi.fn().mockReturnValue("blob:fake-url");
    const revokeObjectURL = vi.fn();
    vi.stubGlobal("URL", { ...URL, createObjectURL, revokeObjectURL });
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});

    render(<ShareImageButton flightId="UAL123-2026-09-12" />);
    fireEvent.click(screen.getByRole("button", { name: /Share as image/ }));

    await vi.waitFor(() => expect(createObjectURL).toHaveBeenCalledWith(FAKE_BLOB));
    expect(clickSpy).toHaveBeenCalledTimes(1);
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:fake-url");

    clickSpy.mockRestore();
    vi.unstubAllGlobals();
  });

  it("shows an error state when fetching the image fails", async () => {
    vi.mocked(api.getFlightCardImageBlob).mockRejectedValue(new Error("network error"));

    render(<ShareImageButton flightId="UAL123-2026-09-12" />);
    fireEvent.click(screen.getByRole("button", { name: /Share as image/ }));

    await screen.findByText("Couldn't generate image");
  });

  it("returns to idle, not an error state, when the user cancels the native share sheet", async () => {
    const canShare = vi.fn().mockReturnValue(true);
    const share = vi.fn().mockRejectedValue(new DOMException("cancelled", "AbortError"));
    Object.assign(navigator, { canShare, share });

    render(<ShareImageButton flightId="UAL123-2026-09-12" />);
    fireEvent.click(screen.getByRole("button", { name: /Share as image/ }));

    await vi.waitFor(() => expect(share).toHaveBeenCalledTimes(1));
    expect(await screen.findByRole("button", { name: "Share as image" })).toBeInTheDocument();
  });
});
