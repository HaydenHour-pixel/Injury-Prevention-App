import { CompletenessStrip } from "../components/CompletenessStrip";
import { DateNavigator } from "../components/DateNavigator";
import { NutritionCard } from "../components/NutritionCard";
import { RecoveryCard } from "../components/RecoveryCard";
import { SleepCard } from "../components/SleepCard";
import { SymptomsCard } from "../components/SymptomsCard";
import { TrainingCard } from "../components/TrainingCard";
import { useDay } from "../hooks/useDay";

/**
 * The whole app: one scrolling page for a single date. Every card saves
 * independently — there is no page-level submit — so `onSaved` on each card
 * just reloads the day payload to pick up what that card wrote.
 */
export function DayView({ date, onNavigate }: { date: string; onNavigate: (date: string) => void }) {
  const { day, loading, error, reload } = useDay(date);

  return (
    <div className="mx-auto max-w-md space-y-3 p-3 pb-8">
      <DateNavigator date={date} onChange={onNavigate} />

      {day && <CompletenessStrip completeness={day.completeness} />}

      {loading && !day && <div className="py-8 text-center text-muted">Loading…</div>}

      {error && (
        <div className="rounded border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger">
          Could not load this day: {error}
        </div>
      )}

      {day && (
        <div className="space-y-3">
          {/* Keyed by date so each card fully remounts on navigation — that's
              what re-seeds its draft-or-server initial state and its "show
              the add form" default, rather than trying to reconcile it via
              props on a persistent instance. */}
          <TrainingCard key={`training-${date}`} date={date} rows={day.training} onSaved={reload} />
          <SleepCard key={`sleep-${date}`} date={date} rows={day.sleep} onSaved={reload} />
          <NutritionCard
            key={`nutrition-${date}`}
            date={date}
            nutrition={day.nutrition}
            onSaved={reload}
          />
          <RecoveryCard key={`recovery-${date}`} date={date} rows={day.recovery} onSaved={reload} />
          <SymptomsCard
            key={`symptoms-${date}`}
            date={date}
            rows={day.symptoms}
            noPainConfirmed={day.no_pain_confirmed}
            onSaved={reload}
          />
        </div>
      )}
    </div>
  );
}
