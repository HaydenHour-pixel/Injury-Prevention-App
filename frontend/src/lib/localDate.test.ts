import { describe, expect, it } from "vitest";
import {
  addDaysToDateString,
  isPastLocalDate,
  parseLocalDateString,
  toLocalDateString,
} from "./localDate";

// Vitest/Node reads process.env.TZ dynamically on each Date call, so setting
// it here (rather than relying on the machine's own timezone) makes this
// test deterministic regardless of where it runs.
process.env.TZ = "America/New_York";

describe("toLocalDateString", () => {
  it("returns the local calendar date, not the UTC date, for a late-evening timestamp", () => {
    // 23:40 on Sept 10 in America/New_York (EDT, UTC-4) is 03:40 UTC on
    // Sept 11 — exactly the bug `new Date().toISOString().split('T')[0]`
    // would hit for an evening log.
    const lateEvening = new Date("2026-09-11T03:40:00Z");

    expect(lateEvening.toISOString().split("T")[0]).toBe("2026-09-11"); // the bug
    expect(toLocalDateString(lateEvening)).toBe("2026-09-10"); // the fix
  });

  it("agrees with the UTC date when nowhere near a day boundary", () => {
    const midday = new Date("2026-09-10T16:00:00Z"); // noon EDT
    expect(toLocalDateString(midday)).toBe("2026-09-10");
  });
});

describe("addDaysToDateString", () => {
  it("advances a day", () => {
    expect(addDaysToDateString("2026-09-10", 1)).toBe("2026-09-11");
  });

  it("goes back a day", () => {
    expect(addDaysToDateString("2026-09-10", -1)).toBe("2026-09-09");
  });

  it("rolls over a month boundary", () => {
    expect(addDaysToDateString("2026-09-30", 1)).toBe("2026-10-01");
  });

  it("rolls over a year boundary", () => {
    expect(addDaysToDateString("2026-12-31", 1)).toBe("2027-01-01");
  });
});

describe("parseLocalDateString", () => {
  it("round-trips through toLocalDateString without shifting a day", () => {
    // The footgun this guards against: `new Date("2026-09-10")` parses as UTC
    // midnight, which reads back as Sept 9 in any negative-UTC-offset zone.
    expect(toLocalDateString(parseLocalDateString("2026-09-10"))).toBe("2026-09-10");
  });
});

describe("isPastLocalDate", () => {
  it("is true for a date before today and false for today or later", () => {
    const yesterday = addDaysToDateString(toLocalDateString(new Date()), -1);
    const today = toLocalDateString(new Date());
    const tomorrow = addDaysToDateString(today, 1);

    expect(isPastLocalDate(yesterday)).toBe(true);
    expect(isPastLocalDate(today)).toBe(false);
    expect(isPastLocalDate(tomorrow)).toBe(false);
  });
});
