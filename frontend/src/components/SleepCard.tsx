import { useMemo, useState } from "react";
import { createSleep, deleteSleep } from "../api/client";
import type { SleepCreate, SleepRead } from "../api/types";
import { useSectionForm } from "../hooks/useSectionForm";
import { Card } from "./Card";
import { RatingPicker } from "./RatingPicker";
import { SaveStatusBadge } from "./SaveStatusBadge";
import { TimeField } from "./TimeField";
import { Toggle } from "./Toggle";

type DraftSleep = Partial<SleepCreate>;
const EMPTY_DRAFT: DraftSleep = { is_nap: false };

/** Hours are computed and displayed, never typed — spec.md's insistence on
 * not asking for anything the athlete can't accurately self-report, and
 * bedtime/wake time already say everything hours would. Handles the overnight
 * wrap (bedtime 23:00, wake 06:30). */
function computeHours(bedtime?: string | null, wakeTime?: string | null): number | null {
  if (!bedtime || !wakeTime) return null;
  const [bh, bm] = bedtime.split(":").map(Number);
  const [wh, wm] = wakeTime.split(":").map(Number);
  let minutes = wh * 60 + wm - (bh * 60 + bm);
  if (minutes <= 0) minutes += 24 * 60;
  return Math.round((minutes / 60) * 100) / 100;
}

export function SleepCard({
  date,
  rows,
  onSaved,
}: {
  date: string;
  rows: SleepRead[];
  onSaved: () => void;
}) {
  const [adding, setAdding] = useState(rows.length === 0);
  const form = useSectionForm<DraftSleep>(date, "sleep", EMPTY_DRAFT);

  const computedHours = useMemo(
    () => computeHours(form.values.bedtime, form.values.wake_time),
    [form.values.bedtime, form.values.wake_time],
  );

  async function handleAdd() {
    const payload: SleepCreate = {
      bedtime: form.values.bedtime,
      wake_time: form.values.wake_time,
      quality_1_to_10: form.values.quality_1_to_10,
      is_nap: form.values.is_nap ?? false,
      hours: computedHours,
    };
    const result = await form.save(() => createSleep(date, payload));
    if (result.ok) {
      form.reset(EMPTY_DRAFT);
      setAdding(false);
      onSaved();
    }
  }

  async function handleDelete(id: number) {
    await deleteSleep(id);
    onSaved();
  }

  return (
    <Card
      title="Sleep"
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
                {r.is_nap ? "Nap" : "Sleep"}
                {r.hours != null ? ` · ${r.hours}h` : ""}
                {r.quality_1_to_10 != null ? ` · quality ${r.quality_1_to_10}/10` : ""}
                {r.bedtime && r.wake_time
                  ? ` · ${r.bedtime.slice(0, 5)}–${r.wake_time.slice(0, 5)}`
                  : ""}
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
            <TimeField
              label="Bedtime"
              value={form.values.bedtime ?? null}
              onChange={(v) => form.update({ bedtime: v })}
            />
            <TimeField
              label="Wake time"
              value={form.values.wake_time ?? null}
              onChange={(v) => form.update({ wake_time: v })}
            />
          </div>
          {computedHours != null && <div className="text-sm text-muted">Computed: {computedHours}h</div>}
          <RatingPicker
            label="Quality"
            value={form.values.quality_1_to_10 ?? null}
            onChange={(v) => form.update({ quality_1_to_10: v })}
          />
          <Toggle
            label="This was a nap"
            checked={form.values.is_nap ?? false}
            onChange={(v) => form.update({ is_nap: v })}
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
