/**
 * A lightweight react-dom render test — no @testing-library/react dependency,
 * just react-dom/client + react's own `act` (both already present via
 * react/react-dom). Enough to prove the preview renders before Save is
 * clickable-with-effect, which a pure-function test of addMealToTotal alone
 * can't demonstrate.
 */
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import * as saveNutritionModule from "../api/saveNutrition";
import type { NutritionRead } from "../api/types";
import { NutritionCard } from "./NutritionCard";

let container: HTMLDivElement;
let root: Root;

beforeEach(() => {
  container = document.createElement("div");
  document.body.appendChild(container);
  root = createRoot(container);
});

afterEach(() => {
  act(() => {
    root.unmount();
  });
  container.remove();
  vi.restoreAllMocks();
});

function typeInto(input: HTMLInputElement, value: string): void {
  const setter = Object.getOwnPropertyDescriptor(
    window.HTMLInputElement.prototype,
    "value",
  )!.set!;
  setter.call(input, value);
  input.dispatchEvent(new Event("input", { bubbles: true }));
}

describe("NutritionCard", () => {
  it("shows the resulting day total (stored + typed) before save is possible", async () => {
    const stored = { protein_g: 100, carbs_g: 200, fat_g: 20, calories: 1500 } as NutritionRead;
    const saveSpy = vi.spyOn(saveNutritionModule, "saveNutrition");

    await act(async () => {
      root.render(<NutritionCard date="2026-09-01" nutrition={stored} onSaved={() => {}} />);
    });

    const proteinInput = container.querySelector(
      'input[aria-label="This meal · Protein (g)"]',
    ) as HTMLInputElement;
    expect(proteinInput).toBeTruthy();

    await act(async () => {
      typeInto(proteinInput, "30");
    });

    // 100 stored + 30 typed = 130 — visible immediately, no save clicked yet.
    expect(container.textContent).toContain("130g protein");
    expect(saveSpy).not.toHaveBeenCalled();
  });

  it("switches to editing the absolute total, not adding to it, via the explicit affordance", async () => {
    const stored = { protein_g: 100, carbs_g: 200, fat_g: 20, calories: 1500 } as NutritionRead;

    await act(async () => {
      root.render(<NutritionCard date="2026-09-02" nutrition={stored} onSaved={() => {}} />);
    });

    const toggle = Array.from(container.querySelectorAll("button")).find(
      (b) => b.textContent === "Edit day total directly",
    ) as HTMLButtonElement;
    await act(async () => {
      toggle.click();
    });

    // Now editing the total directly: fields are pre-seeded with the stored
    // total, and the preview equals whatever is typed, not stored + typed.
    const proteinInput = container.querySelector(
      'input[aria-label="Day total · Protein (g)"]',
    ) as HTMLInputElement;
    expect(proteinInput.value).toBe("100");

    await act(async () => {
      typeInto(proteinInput, "80");
    });

    expect(container.textContent).toContain("80g protein");
    expect(container.textContent).not.toContain("180g protein");
  });
});
