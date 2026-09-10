export function TextField({
  label,
  value,
  onChange,
  multiline = false,
  placeholder,
}: {
  label: string;
  value: string | null;
  onChange: (value: string | null) => void;
  multiline?: boolean;
  placeholder?: string;
}) {
  const commonClassName = "w-full rounded border border-border bg-canvas px-3 text-base text-ink";
  return (
    <label className="block">
      <div className="mb-1 text-sm text-muted">{label}</div>
      {multiline ? (
        <textarea
          value={value ?? ""}
          placeholder={placeholder}
          onChange={(e) => onChange(e.target.value === "" ? null : e.target.value)}
          rows={2}
          className={`${commonClassName} py-2`}
        />
      ) : (
        <input
          type="text"
          value={value ?? ""}
          placeholder={placeholder}
          onChange={(e) => onChange(e.target.value === "" ? null : e.target.value)}
          className={`h-11 ${commonClassName}`}
        />
      )}
    </label>
  );
}
