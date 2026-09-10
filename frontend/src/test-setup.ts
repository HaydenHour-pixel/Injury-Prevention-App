import { afterEach } from "vitest";

// Tells React this environment supports `act()` batching — without it,
// react-dom emits "not configured to support act()" warnings on every
// render in NutritionCard.test.tsx even though the test itself is correct.
declare global {
  var IS_REACT_ACT_ENVIRONMENT: boolean;
}
globalThis.IS_REACT_ACT_ENVIRONMENT = true;

afterEach(() => {
  localStorage.clear();
});
