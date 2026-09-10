import { useState } from "react";
import { createSymptom, deleteSymptom } from "../api/client";
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

function noPainKey(date: string): string {
  return `athlete-tracker:no-pain-confirmed:${date}`;
}

/**
 * Symptoms are the calibration labels (spec.md section 3): retrospective
 * entries get down-weighted, so the UI has two jobs beyond ordinary logging —
 * push for same-day entry, and make the cost of backdating visible rather
 * than blocking it.
 *
 * NOTE: unlike recovery's method_type='none', there is no schema
 * representation for "confirmed no pain" — spec.md section 4 treats "no
 * symptom rows" as that state, which is indistinguishable from "haven't
 * checked yet" at the API level, and Symptom.intensity_1_to_10 is NOT NULL
 * with a 1-10 range, so there's no valid row to POST for "no pain" the way
 * recovery does. "No pain today" below is a local-only acknowledgment
 * (localStorage, per date) purely for the athlete's own UI feedback — it is
 * NOT visible in completeness, the day payload, or from any other device.
 */
export function SymptomsCard({
  date,
  rows,
  onSaved,
}: {
  date: string;
  rows: SymptomRead[];
  onSaved: () => void;
}) {
  const [adding, setAdding] = useState(false);
  const [noPainConfirmed, setNoPainConfirmed] = useState(() => {
    try {
      return localStorage.getItem(noPainKey(date)) === "1";
    } catch {
      return false;
    }
  });
  const form = useSectionForm<DraftSymptom>(date, "symptoms", EMPTY_DRAFT);
  const backdated = isPastLocalDate(date);
  const isToday = date === todayLocalDateString();

  function handleNoPainToday() {
    try {
      localStorage.setItem(noPainKey(date), "1");
    } catch {
      // localStorage unavailable — the visual state below still updates for
      // this session, which is the main point.
    }
    setNoPainConfirmed(true);
  }

  const canSave =
    !!form.values.body_location && !!form.values.type && form.values.intensity_1_to_10 != null;

  async function handleAdd() {
    if (!canSave) return;
    const result = await form.save((data) => createSymptom(date, data as SymptomCreate));
    if (result.ok) {
      form.reset(EMPTY_DRAFT);
      setAdding(false);
      try {
        localStorage.removeItem(noPainKey(date));
      } catch {
        // ignore
      }
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
        <div className="mb-2 grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={handleNoPainToday}
            className={`h-12 rounded border text-sm font-semibold ${
              noPainConfirmed ? "border-good bg-good/15 text-good" : "border-border bg-canvas text-ink"
            }`}
          >
            {noPainConfirmed ? "✓ No pain logged" : isToday ? "No pain today" : "No pain"}
          </button>
          <button
            type="button"
            onClick={() => setAdding(true)}
            className="h-12 rounded border border-accent bg-accent/10 text-sm font-semibold text-accent"
          >
            + Log symptom
          </button>
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
