import { useState } from "react";

/** A numeric field that opens the numeric/decimal keyboard on mobile.
 *
 * Deliberately `type="text"` + `inputMode`, not `type="number"`: the native
 * number input's browser-normalized value (dropped trailing ".", "e" for
 * exponents) fights with keeping an in-progress decimal like "6." on screen
 * while the athlete is still typing "6.2".
 *
 * Owns its own text state, seeded once from `defaultValue`, rather than being
 * fully controlled: re-deriving displayed text from the parsed number on
 * every keystroke is exactly what stomps that in-progress "6." with "6". A
 * fresh value from outside (draft restore, a reset after save) arrives via
 * remounting this field with a new `key`, not via a changing prop.
 *
 * An empty field stays `null`, never 0 — an unfilled field is a value the
 * athlete didn't enter, and 0 is a value they did (spec.md section 4).
 */
export function NumberField({
  label,
  defaultValue,
  onChange,
  integer = false,
  placeholder,
}: {
  label: string;
  defaultValue: number | null;
  onChange: (value: number | null) => void;
  integer?: boolean;
  placeholder?: string;
}) {
  const [text, setText] = useState(defaultValue === null ? "" : String(defaultValue));

  function handleChange(raw: string) {
    setText(raw);
    const normalized = raw.replace(",", ".").trim();
    if (normalized === "" || normalized === "-" || normalized === ".") {
      onChange(null);
      return;
    }
    if (!/^-?\d*\.?\d*$/.test(normalized)) return; // invalid keystroke: ignore, keep last committed value
    const parsed = integer ? parseInt(normalized, 10) : Number(normalized);
    if (!Number.isNaN(parsed)) onChange(parsed);
  }

  return (
    <label className="block">
      <div className="mb-1 text-sm text-muted">{label}</div>
      <input
        type="text"
        inputMode={integer ? "numeric" : "decimal"}
        value={text}
        placeholder={placeholder}
        onChange={(e) => handleChange(e.target.value)}
        className="h-11 w-full rounded border border-border bg-canvas px-3 text-base text-ink"
      />
    </label>
  );
}
