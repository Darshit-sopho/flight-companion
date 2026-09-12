import { useState } from "react";

export function ShareLinkButton() {
  const [copied, setCopied] = useState(false);

  const handleClick = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard API can be unavailable (e.g. insecure context) — fail silently, link is still visible in the address bar.
    }
  };

  return (
    <button type="button" className="share-button" onClick={handleClick}>
      {copied ? "Link copied!" : "Copy shareable link"}
    </button>
  );
}
