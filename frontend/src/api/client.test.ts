import { beforeEach, describe, expect, it, vi } from "vitest";
import { setBackendUrl } from "../lib/backendUrl";
import { getDay } from "./client";
import type { DayResponse } from "./types";

function mockFetchOnce(body: unknown): void {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(body),
      text: () => Promise.resolve(JSON.stringify(body)),
    } as Response),
  );
}

describe("getDay", () => {
  beforeEach(() => {
    setBackendUrl("http://test-backend");
  });

  it("preserves null nutrition, an empty section array, and a method_type='none' row distinctly", async () => {
    const payload: Partial<DayResponse> = {
      date: "2026-09-10",
      daily_entry_exists: true,
      training: [],
      sleep: [],
      nutrition: null,
      no_pain_confirmed: null,
      symptoms: [],
      recovery: [
        {
          id: 1,
          daily_entry_id: 1,
          date: "2026-09-10",
          method_type: "none",
          duration_minutes: null,
          intensity_1_to_10: null,
          applied_at: null,
          symptom_id: null,
          source_confidence: 0.9,
          recall_confidence: 1,
          created_at: "2026-09-10T12:00:00Z",
        },
      ],
      completeness: {
        training: false,
        sleep: false,
        nutrition: false,
        recovery: true,
        symptoms: false,
      },
    };
    mockFetchOnce(payload);

    const result = await getDay("2026-09-10");

    // null stays null — never coerced to an empty object.
    expect(result.nutrition).toBeNull();
    // never-logged sections stay a real empty array, not undefined/null.
    expect(result.training).toEqual([]);
    expect(Array.isArray(result.training)).toBe(true);
    // a method_type='none' row is a populated array, distinct from [].
    expect(result.recovery).toHaveLength(1);
    expect(result.recovery[0].method_type).toBe("none");
  });

  it("keeps an empty recovery array (never opened) distinct from one containing a 'none' row", async () => {
    mockFetchOnce({
      date: "2026-09-11",
      daily_entry_exists: true,
      training: [],
      sleep: [],
      nutrition: null,
      no_pain_confirmed: null,
      symptoms: [],
      recovery: [],
      completeness: {
        training: false,
        sleep: false,
        nutrition: false,
        recovery: false,
        symptoms: false,
      },
    });

    const neverOpened = await getDay("2026-09-11");

    expect(neverOpened.recovery).toEqual([]);
  });
});
