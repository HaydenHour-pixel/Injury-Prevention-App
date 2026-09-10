/** 1-10 ratings are tap-a-number, not a slider — a slider is imprecise
 * one-handed. Every button is large enough to hit with a thumb. */
export function RatingPicker({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number | null;
  onChange: (value: number) => void;
}) {
  return (
    <div>
      <div className="mb-1 text-sm text-muted">{label}</div>
      <div className="grid grid-cols-5 gap-1.5">
        {Array.from({ length: 10 }, (_, i) => i + 1).map((n) => (
          <button
            key={n}
            type="button"
            onClick={() => onChange(n)}
            aria-pressed={value === n}
            className={`h-11 rounded text-base font-medium border ${
              value === n
                ? "border-accent bg-accent text-accent-ink"
                : "border-border bg-canvas text-ink"
            }`}
          >
            {n}
          </button>
        ))}
      </div>
    </div>
  );
}
