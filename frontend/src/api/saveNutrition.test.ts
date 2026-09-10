import { afterEach, describe, expect, it, vi } from "vitest";
import * as client from "./client";
import { saveNutrition } from "./saveNutrition";
import type { DayResponse, NutritionRead } from "./types";

function dayWith(nutrition: NutritionRead | null): DayResponse {
  return {
    date: "2026-09-10",
    daily_entry_exists: true,
    training: [],
    sleep: [],
    recovery: [],
    symptoms: [],
    nutrition,
    completeness: {
      training: false,
      sleep: false,
      nutrition: nutrition !== null,
      recovery: false,
      symptoms: false,
    },
  };
}

describe("saveNutrition", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("PATCHes the existing row when nutrition already exists for the date", async () => {
    const existing = { id: 42 } as NutritionRead;
    vi.spyOn(client, "getDay").mockResolvedValue(dayWith(existing));
    const updateSpy = vi.spyOn(client, "updateNutrition").mockResolvedValue(existing);
    const createSpy = vi.spyOn(client, "createNutrition");

    await saveNutrition("2026-09-10", { protein_g: 30 });

    expect(updateSpy).toHaveBeenCalledWith(42, { protein_g: 30 });
    expect(createSpy).not.toHaveBeenCalled();
  });

  it("POSTs a new row when no nutrition row exists for the date yet", async () => {
    vi.spyOn(client, "getDay").mockResolvedValue(dayWith(null));
    const createSpy = vi.spyOn(client, "createNutrition").mockResolvedValue({} as NutritionRead);
    const updateSpy = vi.spyOn(client, "updateNutrition");

    await saveNutrition("2026-09-10", { protein_g: 30 });

    expect(createSpy).toHaveBeenCalledWith("2026-09-10", { protein_g: 30 });
    expect(updateSpy).not.toHaveBeenCalled();
  });
});
