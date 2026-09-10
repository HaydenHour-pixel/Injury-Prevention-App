import { addDaysToDateString, formatDisplayDate } from "../lib/localDate";

export function DateNavigator({
  date,
  onChange,
}: {
  date: string;
  onChange: (date: string) => void;
}) {
  return (
    <div className="flex items-center gap-2">
      <button
        type="button"
        aria-label="Previous day"
        onClick={() => onChange(addDaysToDateString(date, -1))}
        className="flex h-11 w-11 shrink-0 items-center justify-center rounded border border-border bg-surface text-xl"
      >
        ‹
      </button>

      {/* Tap the date to get the native date picker, layered over the label. */}
      <div className="relative flex-1">
        <div className="pointer-events-none text-center text-lg font-semibold">
          {formatDisplayDate(date)}
        </div>
        <input
          type="date"
          aria-label="Pick a date"
          value={date}
          onChange={(e) => {
            if (e.target.value) onChange(e.target.value);
          }}
          className="absolute inset-0 h-full w-full opacity-0"
        />
      </div>

      <button
        type="button"
        aria-label="Next day"
        onClick={() => onChange(addDaysToDateString(date, 1))}
        className="flex h-11 w-11 shrink-0 items-center justify-center rounded border border-border bg-surface text-xl"
      >
        ›
      </button>
    </div>
  );
}
