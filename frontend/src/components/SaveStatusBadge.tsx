import type { SaveStatus } from "../hooks/useSectionForm";

/** A failed save must never silently discard typed input — this badge is how
 * that failure stays visible, with a retry action right next to it. */
export function SaveStatusBadge({
  status,
  error,
  onRetry,
}: {
  status: SaveStatus;
  error?: string | null;
  onRetry?: () => void;
}) {
  if (status === "idle") return null;

  if (status === "saving") {
    return <span className="text-sm text-muted">Saving…</span>;
  }

  if (status === "saved") {
    return <span className="text-sm text-good">Saved</span>;
  }

  return (
    <span className="flex items-center gap-2 text-sm text-danger">
      Failed to save{error ? `: ${error}` : ""}
      {onRetry && (
        <button type="button" onClick={onRetry} className="underline underline-offset-2">
          Retry
        </button>
      )}
    </span>
  );
}
