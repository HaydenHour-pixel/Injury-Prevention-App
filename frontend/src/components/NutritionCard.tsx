import { useState } from "react";
import { saveNutrition } from "../api/saveNutrition";
import type { NutritionCreate, NutritionRead } from "../api/types";
import { useSectionForm } from "../hooks/useSectionForm";
import { addMealToTotal, EMPTY_MACROS, type NutritionMacros } from "../lib/nutritionTotal";
import { Card } from "./Card";
import { NumberField } from "./NumberField";
import { SaveStatusBadge } from "./SaveStatusBadge";

type Mode = "add-meal" | "edit-total";

interface NutritionDraft {
  mode: Mode;
  values: NutritionMacros;
}

const EMPTY_DRAFT: NutritionDraft = { mode: "add-meal", values: EMPTY_MACROS };

function storedTotal(row: NutritionRead | null): NutritionMacros {
  if (!row) return EMPTY_MACROS;
  return { protein_g: row.protein_g, carbs_g: row.carbs_g, fat_g: row.fat_g, calories: row.calories };
}

function fmt(n: number | null): string {
  return n == null ? "—" : String(n);
}

/**
 * One row per day, always saved as the day's resulting total — never the
 * meal in isolation, since the underlying API is still a single PATCH-or-POST
 * on that one row (no API change needed for this).
 *
 * Default mode enters THIS MEAL's macros and shows the resulting day total
 * live, before save is even possible — that's what stops a double tap (or a
 * second visit for a second meal) from silently double-counting. "Edit day
 * total directly" switches to correcting the absolute total instead, for
 * when the running math itself needs fixing rather than adding to it.
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
  const form = useSectionForm<NutritionDraft>(date, "nutrition", EMPTY_DRAFT);
  const [fieldsKey, setFieldsKey] = useState(0);
  const { mode, values } = form.values;
  const stored = storedTotal(nutrition);

  const resultingTotal = mode === "add-meal" ? addMealToTotal(stored, values) : values;

  function updateField(field: keyof NutritionMacros, value: number | null) {
    form.update({ values: { ...values, [field]: value } });
  }

  function toggleMode() {
    if (mode === "add-meal") {
      form.update({ mode: "edit-total", values: stored });
    } else {
      form.update({ mode: "add-meal", values: EMPTY_MACROS });
    }
    setFieldsKey((k) => k + 1); // force the (intentionally uncontrolled) NumberFields to re-seed
  }

  async function handleSave() {
    const payload: NutritionCreate = resultingTotal;
    const result = await form.save(() => saveNutrition(date, payload));
    if (result.ok) {
      form.reset(EMPTY_DRAFT);
      setFieldsKey((k) => k + 1);
      onSaved();
    }
  }

  const fieldLabel = mode === "add-meal" ? "This meal" : "Day total";

  return (
    <Card
      title="Nutrition"
      action={
        <button
          type="button"
          onClick={toggleMode}
          className="text-xs text-muted underline underline-offset-2"
        >
          {mode === "add-meal" ? "Edit day total directly" : "Cancel"}
        </button>
      }
    >
      <div className="space-y-2">
        <div className="grid grid-cols-2 gap-2" key={fieldsKey}>
          <NumberField
            label={`${fieldLabel} · Protein (g)`}
            defaultValue={values.protein_g}
            onChange={(v) => updateField("protein_g", v)}
          />
          <NumberField
            label={`${fieldLabel} · Carbs (g)`}
            defaultValue={values.carbs_g}
            onChange={(v) => updateField("carbs_g", v)}
          />
          <NumberField
            label={`${fieldLabel} · Fat (g)`}
            defaultValue={values.fat_g}
            onChange={(v) => updateField("fat_g", v)}
          />
          <NumberField
            label={`${fieldLabel} · Calories`}
            integer
            defaultValue={values.calories}
            onChange={(v) => updateField("calories", v)}
          />
        </div>

        {/* The pre-save preview: this is what prevents double-counting on a
            double tap. It reflects the draft on every render, with no
            dependency on a save ever having happened. */}
        <div className="rounded border border-accent/40 bg-accent/10 px-3 py-2">
          <div className="mb-1 text-xs text-muted">
            {mode === "add-meal" ? "Day total after this meal" : "Day total"}
          </div>
          <div className="text-sm font-semibold text-ink">
            {fmt(resultingTotal.protein_g)}g protein · {fmt(resultingTotal.carbs_g)}g carbs ·{" "}
            {fmt(resultingTotal.fat_g)}g fat · {fmt(resultingTotal.calories)} cal
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleSave}
            disabled={form.status === "saving"}
            className="h-11 flex-1 rounded bg-accent text-sm font-semibold text-accent-ink disabled:opacity-50"
          >
            {mode === "add-meal" ? "Save meal" : "Save total"}
          </button>
          <SaveStatusBadge status={form.status} error={form.error} onRetry={handleSave} />
        </div>
        {nutrition == null && mode === "add-meal" && (
          <div className="text-xs text-muted">Not logged yet today</div>
        )}
      </div>
    </Card>
  );
}
