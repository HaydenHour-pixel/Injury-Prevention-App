import { useCallback, useEffect, useState } from "react";
import { getDay } from "../api/client";
import type { DayResponse } from "../api/types";

export function useDay(date: string) {
  const [day, setDay] = useState<DayResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setDay(await getDay(date));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [date]);

  useEffect(() => {
    reload();
  }, [reload]);

  return { day, loading, error, reload };
}
