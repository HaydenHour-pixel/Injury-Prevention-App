import { describe, expect, it } from "vitest";
import { loadDraft } from "./drafts";
import { saveSectionWithDraft } from "./sectionSave";

describe("saveSectionWithDraft", () => {
  it("leaves the draft in localStorage when the save fails", async () => {
    const data = { mileage: 5 };

    const result = await saveSectionWithDraft("2026-09-10", "training", data, async () => {
      throw new Error("network down");
    });

    expect(result.ok).toBe(false);
    expect(loadDraft("2026-09-10", "training")).toEqual(data);
  });

  it("clears the draft once the save succeeds", async () => {
    const data = { mileage: 5 };

    const result = await saveSectionWithDraft("2026-09-10", "training", data, async () => ({}));

    expect(result.ok).toBe(true);
    expect(loadDraft("2026-09-10", "training")).toBeNull();
  });
});
