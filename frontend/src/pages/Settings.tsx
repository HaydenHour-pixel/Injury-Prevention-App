import { useEffect, useState } from "react";
import { getBackendUrl, setBackendUrl } from "../lib/backendUrl";

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

function isIOS(): boolean {
  return /iphone|ipad|ipod/i.test(navigator.userAgent);
}

function isStandalone(): boolean {
  const iosStandalone = (navigator as unknown as { standalone?: boolean }).standalone;
  return window.matchMedia("(display-mode: standalone)").matches || iosStandalone === true;
}

export function Settings() {
  const [url, setUrl] = useState(getBackendUrl());
  const [justSaved, setJustSaved] = useState(false);
  const [installPrompt, setInstallPrompt] = useState<BeforeInstallPromptEvent | null>(null);

  useEffect(() => {
    function handler(e: Event) {
      e.preventDefault();
      setInstallPrompt(e as BeforeInstallPromptEvent);
    }
    window.addEventListener("beforeinstallprompt", handler);
    return () => window.removeEventListener("beforeinstallprompt", handler);
  }, []);

  function handleSaveUrl() {
    setBackendUrl(url);
    setUrl(getBackendUrl());
    setJustSaved(true);
  }

  async function handleInstall() {
    if (!installPrompt) return;
    await installPrompt.prompt();
    setInstallPrompt(null);
  }

  return (
    <div className="mx-auto max-w-md space-y-4 p-3">
      <h1 className="text-lg font-semibold">Settings</h1>

      <section className="rounded-lg border border-border bg-surface p-3">
        <h2 className="mb-2 text-base font-semibold">Backend URL</h2>
        <input
          type="text"
          inputMode="url"
          value={url}
          onChange={(e) => {
            setUrl(e.target.value);
            setJustSaved(false);
          }}
          className="mb-2 h-11 w-full rounded border border-border bg-canvas px-3 text-base text-ink"
        />
        <button
          type="button"
          onClick={handleSaveUrl}
          className="h-11 w-full rounded bg-accent text-sm font-semibold text-accent-ink"
        >
          Save
        </button>
        {justSaved && <div className="mt-2 text-sm text-good">Saved.</div>}
      </section>

      <section className="rounded-lg border border-border bg-surface p-3">
        <h2 className="mb-2 text-base font-semibold">Install</h2>
        {isStandalone() ? (
          <div className="text-sm text-muted">Already installed.</div>
        ) : installPrompt ? (
          <button
            type="button"
            onClick={handleInstall}
            className="h-11 w-full rounded bg-accent text-sm font-semibold text-accent-ink"
          >
            Install app
          </button>
        ) : isIOS() ? (
          <div className="text-sm text-muted">
            Tap the Share icon, then &ldquo;Add to Home Screen&rdquo;.
          </div>
        ) : (
          <div className="text-sm text-muted">
            Not installable right now — your browser may not support it, or the prompt was already
            dismissed this session.
          </div>
        )}
      </section>
    </div>
  );
}
