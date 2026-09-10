import { useState } from "react";
import { loadDraft, saveDraft, type Section } from "../lib/drafts";
import { saveSectionWithDraft } from "../lib/sectionSave";

export type SaveStatus = "idle" | "saving" | "saved" | "error";

/**
 * Shared behavior for every section card's "add new" form: restore a draft on
 * mount, persist every edit as a draft, and on save keep the draft unless the
 * save actually succeeds. Callers remount this (via a `key={date}` on the
 * card) when the date changes, rather than this hook re-seeding itself.
 */
export function useSectionForm<T>(date: string, section: Section, initialValue: T) {
  const [values, setValuesRaw] = useState<T>(() => loadDraft<T>(date, section) ?? initialValue);
  const [status, setStatus] = useState<SaveStatus>("idle");
  const [error, setError] = useState<string | null>(null);

  /** User-driven edits: persists a draft on every change. */
  function update(patch: Partial<T>) {
    setValuesRaw((prev) => {
      const next = { ...prev, ...patch };
      saveDraft(date, section, next);
      return next;
    });
  }

  /** Programmatic resets (e.g. clearing the form after a successful add, or
   * seeding from a freshly-fetched server row) — does not touch the draft. */
  function reset(next: T) {
    setValuesRaw(next);
    setStatus("idle");
    setError(null);
  }

  async function save(action: (data: T) => Promise<unknown>) {
    setStatus("saving");
    setError(null);
    const result = await saveSectionWithDraft(date, section, values, action);
    setStatus(result.ok ? "saved" : "error");
    if (!result.ok) {
      setError(result.error instanceof Error ? result.error.message : "Save failed");
    }
    return result;
  }

  return { values, update, reset, status, error, save };
}
