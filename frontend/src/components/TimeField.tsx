export function TimeField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string | null;
  onChange: (value: string | null) => void;
}) {
  return (
    <label className="block">
      <div className="mb-1 text-sm text-muted">{label}</div>
      <input
        type="time"
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value === "" ? null : e.target.value)}
        className="h-11 w-full rounded border border-border bg-canvas px-3 text-base text-ink"
      />
    </label>
  );
}
