/** A row of tap targets for choosing one of a fixed set of string values —
 * used for method type, pain type, onset. Large targets, no dropdown/select
 * (a native <select> is a poor one-handed target and hides the options). */
export function ButtonGroup<T extends string>({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: { value: T; label: string }[];
  value: T | null;
  onChange: (value: T) => void;
}) {
  return (
    <div>
      <div className="mb-1 text-sm text-muted">{label}</div>
      <div className="flex flex-wrap gap-1.5">
        {options.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(opt.value)}
            aria-pressed={value === opt.value}
            className={`h-11 rounded border px-3 text-sm font-medium ${
              value === opt.value
                ? "border-accent bg-accent text-accent-ink"
                : "border-border bg-canvas text-ink"
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}
