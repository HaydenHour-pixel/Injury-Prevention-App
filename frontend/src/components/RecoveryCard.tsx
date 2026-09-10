import { useState } from "react";
import { createRecovery, deleteRecovery } from "../api/client";
import type { RecoveryCreate, RecoveryMethodType, RecoveryRead } from "../api/types";
import { useSectionForm } from "../hooks/useSectionForm";
import { ButtonGroup } from "./ButtonGroup";
import { Card } from "./Card";
import { NumberField } from "./NumberField";
import { RatingPicker } from "./RatingPicker";
import { SaveStatusBadge } from "./SaveStatusBadge";

const METHOD_OPTIONS: { value: RecoveryMethodType; label: string }[] = [
  { value: "foam_roll", label: "Foam roll" },
  { value: "yoga", label: "Yoga" },
  { value: "ice_bath", label: "Ice bath" },
  { value: "massage", label: "Massage" },
  { value: "stretching", label: "Stretching" },
  { value: "rest", label: "Rest" },
];

type DraftRecovery = Partial<RecoveryCreate>;

const EMPTY_DRAFT: DraftRecovery = {};

/**
 * The whole schema distinguishes "did no recovery" (a row with
 * method_type='none') from "never opened the section" (no row). The
 * "No recovery today" button is how that first state gets recorded, and it
 * gets equal visual weight to logging a real method — if it's buried, it
 * gets skipped, and the recovery-adequacy ratio (spec.md section 5.4) ends up
 * computed against data that's silently missing rather than genuinely zero.
 */
export function RecoveryCard({
  date,
  rows,
  onSaved,
}: {
  date: string;
  rows: RecoveryRead[];
  onSaved: () => void;
}) {
  const [adding, setAdding] = useState(false);
  const [noneStatus, setNoneStatus] = useState<"idle" | "saving" | "error">("idle");
  const form = useSectionForm<DraftRecovery>(date, "recovery", EMPTY_DRAFT);

  const loggedNone = rows.some((r) => r.method_type === "none");
  const realRows = rows.filter((r) => r.method_type !== "none");

  async function handleNoRecoveryToday() {
    setNoneStatus("saving");
    try {
      await createRecovery(date, { method_type: "none" });
      setNoneStatus("idle");
      onSaved();
    } catch {
      setNoneStatus("error");
    }
  }

  async function handleAddMethod() {
    if (!form.values.method_type) return;
    const result = await form.save((data) => createRecovery(date, data as RecoveryCreate));
    if (result.ok) {
      form.reset(EMPTY_DRAFT);
      setAdding(false);
      onSaved();
    }
  }

  async function handleDelete(id: number) {
    await deleteRecovery(id);
    onSaved();
  }

  return (
    <Card title="Recovery">
      <div className="mb-2 grid grid-cols-2 gap-2">
        <button
          type="button"
          onClick={handleNoRecoveryToday}
          disabled={noneStatus === "saving"}
          className={`h-12 rounded border text-sm font-semibold ${
            loggedNone ? "border-good bg-good/15 text-good" : "border-border bg-canvas text-ink"
          }`}
        >
          {loggedNone ? "✓ Logged: no recovery" : "No recovery today"}
        </button>
        <button
          type="button"
          onClick={() => setAdding((a) => !a)}
          className="h-12 rounded border border-accent bg-accent/10 text-sm font-semibold text-accent"
        >
          + Log a method
        </button>
      </div>

      {noneStatus === "error" && (
        <div className="mb-2">
          <SaveStatusBadge status="error" error="Could not save" onRetry={handleNoRecoveryToday} />
        </div>
      )}

      {realRows.length > 0 && (
        <ul className="mb-2 space-y-1">
          {realRows.map((r) => (
            <li
              key={r.id}
              className="flex items-center justify-between rounded border border-border px-2 py-1.5 text-sm"
            >
              <span>
                {METHOD_OPTIONS.find((m) => m.value === r.method_type)?.label ?? r.method_type}
                {r.duration_minutes != null ? ` · ${r.duration_minutes}min` : ""}
                {r.intensity_1_to_10 != null ? ` · felt ${r.intensity_1_to_10}/10` : ""}
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

      {adding && (
        <div className="space-y-2 border-t border-border pt-2">
          <ButtonGroup
            label="Method"
            options={METHOD_OPTIONS}
            value={form.values.method_type ?? null}
            onChange={(v) => form.update({ method_type: v })}
          />
          <NumberField
            label="Duration (minutes)"
            integer
            defaultValue={form.values.duration_minutes ?? null}
            onChange={(v) => form.update({ duration_minutes: v })}
          />
          <RatingPicker
            label="Felt intensity (optional)"
            value={form.values.intensity_1_to_10 ?? null}
            onChange={(v) => form.update({ intensity_1_to_10: v })}
          />
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={handleAddMethod}
              disabled={!form.values.method_type || form.status === "saving"}
              className="h-11 flex-1 rounded bg-accent text-sm font-semibold text-accent-ink disabled:opacity-50"
            >
              Save
            </button>
            <SaveStatusBadge status={form.status} error={form.error} onRetry={handleAddMethod} />
          </div>
        </div>
      )}
    </Card>
  );
}
