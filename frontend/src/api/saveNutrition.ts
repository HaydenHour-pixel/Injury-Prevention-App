import { createNutrition, getDay, updateNutrition } from "./client";
import type { NutritionCreate, NutritionRead, NutritionUpdate } from "./types";

/**
 * Nutrition is one row per day; the backend 409s on a second POST. This is
 * the common path, not an edge case — lunch and dinner get logged separately,
 * so the row usually already exists by the time the second entry is saved.
 *
 * Always re-fetches the day rather than trusting a possibly-stale prop:
 * whether the row exists can change between when the card last rendered and
 * when the athlete taps save.
 */
export async function saveNutrition(
  date: string,
  values: NutritionCreate | NutritionUpdate,
): Promise<NutritionRead> {
  const day = await getDay(date);
  if (day.nutrition) {
    return updateNutrition(day.nutrition.id, values as NutritionUpdate);
  }
  return createNutrition(date, values as NutritionCreate);
}
