import { saveNutrition } from "../api/saveNutrition";
import type { NutritionCreate, NutritionRead } from "../api/types";
import { useSectionForm } from "../hooks/useSectionForm";
import { Card } from "./Card";
import { NumberField } from "./NumberField";
import { SaveStatusBadge } from "./SaveStatusBadge";

type DraftNutrition = Partial<NutritionCreate>;

function toDraft(row: NutritionRead | null): DraftNutrition {
  if (!row) return {};
  return { protein_g: row.protein_g, carbs_g: row.carbs_g, fat_g: row.fat_g, calories: row.calories };
}

/**
 * One row per day. Lunch and dinner get logged separately, so re-editing the
 * running total (PATCH) is the common path here, not the edge case — the
 * save orchestration (GET, then PATCH-or-POST) lives in api/saveNutrition.ts
 * so it's independently testable.
 */
export function NutritionCard({
  date,
  nutrition,
  onSaved,
}: {
  date: string;
  nutrition: NutritionRead | null;
  onSaved: () => void;
}) {
  const form = useSectionForm<DraftNutrition>(date, "nutrition", toDraft(nutrition));

  async function handleSave() {
    const result = await form.save((data) => saveNutrition(date, data as NutritionCreate));
    if (result.ok) onSaved();
  }

  return (
    <Card title="Nutrition">
      <div className="space-y-2">
        <div className="grid grid-cols-2 gap-2">
          <NumberField
            label="Protein (g)"
            defaultValue={form.values.protein_g ?? null}
            onChange={(v) => form.update({ protein_g: v })}
          />
          <NumberField
            label="Carbs (g)"
            defaultValue={form.values.carbs_g ?? null}
            onChange={(v) => form.update({ carbs_g: v })}
          />
          <NumberField
            label="Fat (g)"
            defaultValue={form.values.fat_g ?? null}
            onChange={(v) => form.update({ fat_g: v })}
          />
          <NumberField
            label="Calories"
            integer
            defaultValue={form.values.calories ?? null}
            onChange={(v) => form.update({ calories: v })}
          />
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleSave}
            disabled={form.status === "saving"}
            className="h-11 flex-1 rounded bg-accent text-sm font-semibold text-accent-ink disabled:opacity-50"
          >
            {nutrition ? "Update" : "Save"}
          </button>
          <SaveStatusBadge status={form.status} error={form.error} onRetry={handleSave} />
        </div>
        {nutrition == null && <div className="text-xs text-muted">Not logged yet today</div>}
      </div>
    </Card>
  );
}
