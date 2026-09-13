import { useState } from "react";

import { api } from "../api/client";

interface Props {
  flightId: string;
}

type ButtonState = "idle" | "working" | "error";

/** SC-D3: casual "share to a chat" image. Uses the Web Share API's file-sharing support where available
 * (mobile Safari/Chrome), and falls back to a plain browser download elsewhere (desktop). The PNG itself
 * is rendered server-side (see backend/app/services/card_image_service.py) -- this component only
 * fetches it and hands it to whichever share mechanism the browser supports.
 */
export function ShareImageButton({ flightId }: Props) {
  const [state, setState] = useState<ButtonState>("idle");

  const handleClick = async () => {
    setState("working");
    try {
      const blob = await api.getFlightCardImageBlob(flightId);
      const file = new File([blob], `flight-${flightId}.png`, { type: "image/png" });

      if (navigator.canShare?.({ files: [file] })) {
        await navigator.share({ files: [file], title: "Flight status" });
      } else {
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `flight-${flightId}.png`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
      }
      setState("idle");
    } catch (err) {
      // A user cancelling the native share sheet also rejects navigator.share() -- that's not a real
      // error, just don't leave the button stuck in "Generating…".
      if (err instanceof DOMException && err.name === "AbortError") {
        setState("idle");
        return;
      }
      setState("error");
    }
  };

  return (
    <button type="button" className="share-button" onClick={handleClick} disabled={state === "working"}>
      {state === "working" ? "Generating…" : state === "error" ? "Couldn't generate image" : "Share as image"}
    </button>
  );
}
