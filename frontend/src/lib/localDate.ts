/**
 * The athlete's local calendar date — never derived from a UTC timestamp.
 *
 * `new Date().toISOString().split('T')[0]` returns the UTC date. At 11:40pm
 * Eastern that's already tomorrow in UTC, which would misfile a logging
 * session under the wrong day. `Date`'s plain getters (getFullYear/getMonth/
 * getDate, as opposed to their getUTC* counterparts) read the date in the
 * runtime's local timezone — which, on the athlete's own phone, is the
 * athlete's timezone. That's the fix: use those getters, never toISOString,
 * anywhere a calendar day is needed.
 */

const pad2 = (n: number): string => String(n).padStart(2, "0");

/** Formats a Date as YYYY-MM-DD using its LOCAL calendar date. */
export function toLocalDateString(date: Date): string {
  return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())}`;
}

/** Today's date, in the local calendar — the one and only place `new Date()`
 * (no arguments) should be called for "what day is it". */
export function todayLocalDateString(): string {
  return toLocalDateString(new Date());
}

/** Adds `days` (may be negative) to a YYYY-MM-DD string, staying in local
 * calendar terms throughout — used by the date navigator's prev/next.
 */
export function addDaysToDateString(dateString: string, days: number): string {
  const [year, month, day] = dateString.split("-").map(Number);
  // Constructing via the local (non-UTC) Date constructor and adding to
  // `day` lets JS normalize month/year rollovers; reading back via the local
  // getters above keeps this consistent with toLocalDateString.
  const d = new Date(year, month - 1, day + days);
  return toLocalDateString(d);
}

/** True if `dateString` (YYYY-MM-DD) is strictly before today's local date. */
export function isPastLocalDate(dateString: string): boolean {
  return dateString < todayLocalDateString();
}

/**
 * Parses a YYYY-MM-DD string as a local midnight `Date`.
 *
 * `new Date("2026-09-10")` (the obvious-looking way) parses as UTC midnight,
 * so `.getDate()` on it shows the *previous* day in any negative-UTC-offset
 * timezone — the same family of bug this module exists to prevent. Always go
 * through this function to turn a date string back into a `Date`.
 */
export function parseLocalDateString(dateString: string): Date {
  const [year, month, day] = dateString.split("-").map(Number);
  return new Date(year, month - 1, day);
}

/** "Thu, Sep 10" — for the date navigator's label. */
export function formatDisplayDate(dateString: string): string {
  return new Intl.DateTimeFormat(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
  }).format(parseLocalDateString(dateString));
}
