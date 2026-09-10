/**
 * In-progress form state, persisted to localStorage keyed by (date, section)
 * and restored on load. This is a draft store, not an offline write queue:
 * nothing here retries a network request on its own, and there is no
 * conflict resolution — see the section cards for the retry-on-failure UI.
 *
 * A failed save must never silently discard typed input, so callers clear a
 * draft only after a *successful* save, never after a failed one.
 */

export type Section = "training" | "sleep" | "nutrition" | "recovery" | "symptoms";

function draftKey(date: string, section: Section): string {
  return `athlete-tracker:draft:${date}:${section}`;
}

export function saveDraft<T>(date: string, section: Section, data: T): void {
  try {
    localStorage.setItem(draftKey(date, section), JSON.stringify(data));
  } catch {
    // Quota exceeded, private-browsing storage lockout, etc. Losing the draft
    // cache is not fatal — the user's typed input is still on screen — so
    // this fails silently rather than crashing the form.
  }
}

export function loadDraft<T>(date: string, section: Section): T | null {
  try {
    const raw = localStorage.getItem(draftKey(date, section));
    return raw === null ? null : (JSON.parse(raw) as T);
  } catch {
    return null;
  }
}

export function clearDraft(date: string, section: Section): void {
  try {
    localStorage.removeItem(draftKey(date, section));
  } catch {
    // ignore
  }
}
