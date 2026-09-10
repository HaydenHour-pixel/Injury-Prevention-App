import { useEffect, useState } from "react";
import { createSymptom, deleteSymptom, setNoPainConfirmed } from "../api/client";
import type { PainOnset, PainType, SymptomCreate, SymptomRead } from "../api/types";
import { useSectionForm } from "../hooks/useSectionForm";
import { isPastLocalDate, todayLocalDateString } from "../lib/localDate";
import { ButtonGroup } from "./ButtonGroup";
import { Card } from "./Card";
import { RatingPicker } from "./RatingPicker";
import { SaveStatusBadge } from "./SaveStatusBadge";
import { TextField } from "./TextField";
import { Toggle } from "./Toggle";

const TYPE_OPTIONS: { value: PainType; label: string }[] = [
  { value: "muscle_soreness", label: "Muscle soreness" },
  { value: "dull_ache", label: "Dull ache" },
  { value: "sharp_pain", label: "Sharp pain" },
];

const ONSET_OPTIONS: { value: PainOnset; label: string }[] = [
  { value: "sudden", label: "Sudden" },
  { value: "gradual", label: "Gradual" },
  { value: "unknown", label: "Unknown" },
];

type DraftSymptom = Partial<SymptomCreate>;
const EMPTY_DRAFT: DraftSymptom = { limiting: false, active: true };

function noPainCacheKey(date: string): string {
  return `athlete-tracker:no-pain-confirmed:${date}`;
}

function readNoPainCache(date: string): boolean {
  try {
    return localStorage.getItem(noPainCacheKey(date)) === "1";
  } catch {
    return false;
  }
}

function writeNoPainCache(date: string, value: boolean): void {
  try {
    if (value) {
      localStorage.setItem(noPainCacheKey(date), "1");
    } else {
      localStorage.removeItem(noPainCacheKey(date));
    }
  } catch {
    // Quota exceeded or storage unavailable — the confirmation is still
    // persisted server-side; this cache is only for perceived responsiveness.
  }
}

/**
 * Symptoms are the calibration labels (spec.md section 3): retrospective
 * entries get down-weighted, so the UI has two jobs beyond ordinary logging —
 * push for same-day entry, and make the cost of backdating visible rather
 * than blocking it.
 *
 * "No pain today" persists to `daily_entry.no_pain_confirmed` (spec.md
 * section 4) — an unlogged painful day must not read the same, at
 * calibration time, as an explicit confirmation. localStorage here is only
 * an optimistic-UI cache: it paints "confirmed" instantly on tap and
 * survives an app close/reopen during the brief in-flight window, but the
 * `noPainConfirmed` prop (sourced from the day payload) is always resynced
 * to match the server the moment it's known.
 */
export function SymptomsCard({
  date,
  rows,
  noPainConfirmed,
  onSaved,
}: {
  date: string;
  rows: SymptomRead[];
  noPainConfirmed: boolean | null;
  onSaved: () => void;
}) {
  const [adding, setAdding] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [optimisticNoPain, setOptimisticNoPain] = useState(() => readNoPainCache(date));
  const form = useSectionForm<DraftSymptom>(date, "symptoms", EMPTY_DRAFT);
  const backdated = isPastLocalDate(date);
  const isToday = date === todayLocalDateString();

  useEffect(() => {
    // The server value just arrived (initial load, or after a reload
    // triggered by this tap or by logging a symptom elsewhere) — resync the
    // cache and drop any stale optimism so a later legitimate clear-to-null
    // isn't masked by a leftover "confirmed" cache entry.
    writeNoPainCache(date, noPainConfirmed === true);
    setOptimisticNoPain(noPainConfirmed === true);
  }, [date, noPainConfirmed]);

  const displayedNoPain = noPainConfirmed === true || optimisticNoPain;

  async function handleNoPainToday() {
    setSaving(true);
    setSaveError(null);
    setOptimisticNoPain(true);
    writeNoPainCache(date, true);
    try {
      await setNoPainConfirmed(date, true);
      onSaved();
    } catch (err) {
      setOptimisticNoPain(false);
      writeNoPainCache(date, false);
      setSaveError(err instanceof Error ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  }

  const canSave =
    !!form.values.body_location && !!form.values.type && form.values.intensity_1_to_10 != null;

  async function handleAdd() {
    if (!canSave) return;
    const result = await form.save((data) => createSymptom(date, data as SymptomCreate));
    if (result.ok) {
      form.reset(EMPTY_DRAFT);
      setAdding(false);
      // The backend clears a standing no_pain_confirmed to NULL when a
      // symptom is created; onSaved's reload brings that back as a fresh
      // `noPainConfirmed` prop, which the effect above resyncs the cache to.
      onSaved();
    }
  }

  async function handleDelete(id: number) {
    await deleteSymptom(id);
    onSaved();
  }

  return (
    <Card title="Symptoms">
      {backdated && (
        <div className="mb-2 rounded border border-danger/40 bg-danger/10 px-2 py-1.5 text-xs text-danger">
          Backdated entry — will carry reduced confidence as a calibration label
        </div>
      )}

      {rows.length === 0 && !adding && (
        <div className="mb-2 space-y-2">
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={handleNoPainToday}
              disabled={saving || displayedNoPain}
              className={`h-12 rounded border text-sm font-semibold disabled:opacity-80 ${
                displayedNoPain
                  ? "border-good bg-good/15 text-good"
                  : "border-border bg-canvas text-ink"
              }`}
            >
              {displayedNoPain ? "✓ No pain logged" : isToday ? "No pain today" : "No pain"}
            </button>
            <button
              type="button"
              onClick={() => setAdding(true)}
              className="h-12 rounded border border-accent bg-accent/10 text-sm font-semibold text-accent"
            >
              + Log symptom
            </button>
          </div>
          {saveError && (
            <SaveStatusBadge status="error" error={saveError} onRetry={handleNoPainToday} />
          )}
        </div>
      )}

      {rows.length > 0 && (
        <ul className="mb-2 space-y-1">
          {rows.map((r) => (
            <li
              key={r.id}
              className="flex items-center justify-between rounded border border-border px-2 py-1.5 text-sm"
            >
              <span>
                {r.body_location} · {TYPE_OPTIONS.find((t) => t.value === r.type)?.label ?? r.type} ·{" "}
                {r.intensity_1_to_10}/10
                {r.limiting ? " · limiting" : ""}
              </span>
              <button
                type="button"
                onClick={() => handleDelete(r.id)}
                aria-label="Delete"
                className="px-2 text-muted"
              >
                ✕
              </button>
            </li>
          ))}
        </ul>
      )}

      {rows.length > 0 && !adding && (
        <button
          type="button"
          onClick={() => setAdding(true)}
          className="h-11 w-full rounded border border-accent bg-accent/10 text-sm font-semibold text-accent"
        >
          + Log another
        </button>
      )}

      {adding && (
        <div className="space-y-2 border-t border-border pt-2">
          <TextField
            label="Location"
            value={form.values.body_location ?? null}
            onChange={(v) => form.update({ body_location: v ?? undefined })}
            placeholder="left knee"
          />
          <ButtonGroup
            label="Type"
            options={TYPE_OPTIONS}
            value={form.values.type ?? null}
            onChange={(v) => form.update({ type: v })}
          />
          <RatingPicker
            label="Intensity"
            value={form.values.intensity_1_to_10 ?? null}
            onChange={(v) => form.update({ intensity_1_to_10: v })}
          />
          <ButtonGroup
            label="Onset (optional)"
            options={ONSET_OPTIONS}
            value={form.values.onset ?? null}
            onChange={(v) => form.update({ onset: v })}
          />
          <Toggle
            label="Limiting activity"
            checked={form.values.limiting ?? false}
            onChange={(v) => form.update({ limiting: v })}
          />
          <TextField
            label="Description (optional)"
            value={form.values.description ?? null}
            onChange={(v) => form.update({ description: v })}
            multiline
          />
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={handleAdd}
              disabled={!canSave || form.status === "saving"}
              className="h-11 flex-1 rounded bg-accent text-sm font-semibold text-accent-ink disabled:opacity-50"
            >
              Save
            </button>
            <SaveStatusBadge status={form.status} error={form.error} onRetry={handleAdd} />
            <button type="button" onClick={() => setAdding(false)} className="text-sm text-muted">
              Cancel
            </button>
          </div>
        </div>
      )}
    </Card>
  );
}
