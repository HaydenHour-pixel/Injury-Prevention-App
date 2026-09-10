import type { Completeness } from "../api/types";

const SECTIONS: { key: keyof Completeness; label: string }[] = [
  { key: "training", label: "Training" },
  { key: "sleep", label: "Sleep" },
  { key: "nutrition", label: "Nutrition" },
  { key: "recovery", label: "Recovery" },
  { key: "symptoms", label: "Symptoms" },
];

export function CompletenessStrip({ completeness }: { completeness: Completeness }) {
  return (
    <div className="flex gap-1.5">
      {SECTIONS.map(({ key, label }) => (
        <div
          key={key}
          className={`flex-1 rounded border py-1 text-center text-[11px] font-medium ${
            completeness[key]
              ? "border-accent bg-accent/15 text-accent"
              : "border-border bg-surface text-muted"
          }`}
        >
          {label}
        </div>
      ))}
    </div>
  );
}
