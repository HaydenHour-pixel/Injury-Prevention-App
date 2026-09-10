import { useCallback, useEffect, useState } from "react";
import { todayLocalDateString } from "./lib/localDate";
import { DayView } from "./pages/DayView";
import { Settings } from "./pages/Settings";

/**
 * Two screens, one dynamic param — not enough surface to justify a router
 * dependency. Plain History API + popstate.
 */
function useRoute() {
  const [path, setPath] = useState(() => window.location.pathname);

  useEffect(() => {
    function onPopState() {
      setPath(window.location.pathname);
    }
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const navigate = useCallback((to: string) => {
    window.history.pushState({}, "", to);
    setPath(to);
  }, []);

  return { path, navigate };
}

const DAY_ROUTE = /^\/day\/(\d{4}-\d{2}-\d{2})$/;

export default function App() {
  const { path, navigate } = useRoute();

  if (path === "/settings") {
    return <Settings />;
  }

  const match = path.match(DAY_ROUTE);
  const date = match ? match[1] : todayLocalDateString();

  return (
    <div className="min-h-screen">
      <DayView date={date} onNavigate={(d) => navigate(`/day/${d}`)} />
      <nav className="mx-auto flex max-w-md justify-center border-t border-border p-3">
        <button
          type="button"
          onClick={() => navigate("/settings")}
          className="text-sm text-muted underline underline-offset-2"
        >
          Settings
        </button>
      </nav>
    </div>
  );
}
