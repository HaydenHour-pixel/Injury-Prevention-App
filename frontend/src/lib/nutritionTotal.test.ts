import { describe, expect, it } from "vitest";
import { addMealToTotal, EMPTY_MACROS } from "./nutritionTotal";

describe("addMealToTotal", () => {
  it("adds a second meal's macros onto the stored day total", () => {
    const stored = { protein_g: 100, carbs_g: 200, fat_g: 20, calories: 1500 };
    const meal = { protein_g: 30, carbs_g: 40, fat_g: 5, calories: 350 };

    expect(addMealToTotal(stored, meal)).toEqual({
      protein_g: 130,
      carbs_g: 240,
      fat_g: 25,
      calories: 1850,
    });
  });

  it("leaves a field untouched by either side as null, not 0", () => {
    const stored = { protein_g: 100, carbs_g: null, fat_g: null, calories: null };
    const meal = { protein_g: null, carbs_g: 40, fat_g: null, calories: null };

    expect(addMealToTotal(stored, meal)).toEqual({
      protein_g: 100,
      carbs_g: 40,
      fat_g: null,
      calories: null,
    });
  });

  it("equals the meal itself when nothing was stored yet", () => {
    const meal = { protein_g: 30, carbs_g: 40, fat_g: 5, calories: 350 };
    expect(addMealToTotal(EMPTY_MACROS, meal)).toEqual(meal);
  });
});
