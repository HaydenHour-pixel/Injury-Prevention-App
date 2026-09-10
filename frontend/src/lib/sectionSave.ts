import { clearDraft, saveDraft, type Section } from "./drafts";

export interface SectionSaveResult {
  ok: boolean;
  error?: unknown;
}

/**
 * The shared save contract for every section card: persist the draft first,
 * attempt the save, and clear the draft only on success. A failed save must
 * never silently discard typed input (hence saving the draft unconditionally
 * up front, before the network call can fail).
 */
export async function saveSectionWithDraft<T>(
  date: string,
  section: Section,
  data: T,
  action: (data: T) => Promise<unknown>,
): Promise<SectionSaveResult> {
  saveDraft(date, section, data);
  try {
    await action(data);
    clearDraft(date, section);
    return { ok: true };
  } catch (error) {
    return { ok: false, error };
  }
}
