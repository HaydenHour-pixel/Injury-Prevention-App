export interface NutritionMacros {
  protein_g: number | null;
  carbs_g: number | null;
  fat_g: number | null;
  calories: number | null;
}

export const EMPTY_MACROS: NutritionMacros = {
  protein_g: null,
  carbs_g: null,
  fat_g: null,
  calories: null,
};

function sum(a: number | null, b: number | null): number | null {
  if (a == null && b == null) return null;
  return (a ?? 0) + (b ?? 0);
}

/**
 * The day's resulting total once `meal` is added to whatever's already
 * stored. Both sides may be partially filled — an athlete might log only
 * protein for a snack and leave the rest blank — so a field neither side
 * touched stays `null` rather than becoming 0 (spec.md section 4).
 */
export function addMealToTotal(stored: NutritionMacros, meal: NutritionMacros): NutritionMacros {
  return {
    protein_g: sum(stored.protein_g, meal.protein_g),
    carbs_g: sum(stored.carbs_g, meal.carbs_g),
    fat_g: sum(stored.fat_g, meal.fat_g),
    calories: sum(stored.calories, meal.calories),
  };
}
