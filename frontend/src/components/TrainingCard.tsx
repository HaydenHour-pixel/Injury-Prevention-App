import { useState } from "react";
import { createTraining, deleteTraining } from "../api/client";
import type { TrainingCreate, TrainingRead } from "../api/types";
import { useSectionForm } from "../hooks/useSectionForm";
import { Card } from "./Card";
import { NumberField } from "./NumberField";
import { RatingPicker } from "./RatingPicker";
import { SaveStatusBadge } from "./SaveStatusBadge";
import { TextField } from "./TextField";

type DraftTraining = Partial<TrainingCreate>;
const EMPTY_DRAFT: DraftTraining = {};

export function TrainingCard({
  date,
  rows,
  onSaved,
}: {
  date: string;
  rows: TrainingRead[];
  onSaved: () => void;
}) {
  const [adding, setAdding] = useState(rows.length === 0);
  const form = useSectionForm<DraftTraining>(date, "training", EMPTY_DRAFT);

  async function handleAdd() {
    const result = await form.save((data) => createTraining(date, data as TrainingCreate));
    if (result.ok) {
      form.reset(EMPTY_DRAFT);
      setAdding(false);
      onSaved();
    }
  }

  async function handleDelete(id: number) {
    await deleteTraining(id);
    onSaved();
  }

  return (
    <Card
      title="Training"
      action={
        !adding && (
          <button
            type="button"
            onClick={() => setAdding(true)}
            className="h-9 rounded border border-accent bg-accent/10 px-3 text-sm font-semibold text-accent"
          >
            + Log
          </button>
        )
      }
    >
      {rows.length > 0 && (
        <ul className="mb-2 space-y-1">
          {rows.map((r) => (
            <li
              key={r.id}
              className="flex items-center justify-between rounded border border-border px-2 py-1.5 text-sm"
            >
              <span>
                {r.mileage != null ? `${r.mileage}mi` : "no mileage"}
                {r.intensity_1_to_10 != null ? ` · intensity ${r.intensity_1_to_10}/10` : ""}
                {r.elevation_gain_ft != null ? ` · ${r.elevation_gain_ft}ft` : ""}
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
        <div className="space-y-2">
          <div className="grid grid-cols-2 gap-2">
            <NumberField
              label="Miles"
              defaultValue={form.values.mileage ?? null}
              onChange={(v) => form.update({ mileage: v })}
            />
            <NumberField
              label="Elevation (ft, optional)"
              integer
              defaultValue={form.values.elevation_gain_ft ?? null}
              onChange={(v) => form.update({ elevation_gain_ft: v })}
            />
          </div>
          <RatingPicker
            label="Intensity"
            value={form.values.intensity_1_to_10 ?? null}
            onChange={(v) => form.update({ intensity_1_to_10: v })}
          />
          <TextField
            label="Notes (optional)"
            value={form.values.notes ?? null}
            onChange={(v) => form.update({ notes: v })}
            multiline
          />
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={handleAdd}
              disabled={form.status === "saving"}
              className="h-11 flex-1 rounded bg-accent text-sm font-semibold text-accent-ink disabled:opacity-50"
            >
              Save
            </button>
            <SaveStatusBadge status={form.status} error={form.error} onRetry={handleAdd} />
            {rows.length > 0 && (
              <button type="button" onClick={() => setAdding(false)} className="text-sm text-muted">
                Cancel
              </button>
            )}
          </div>
        </div>
      )}
    </Card>
  );
}
