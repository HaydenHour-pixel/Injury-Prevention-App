/** The backend's base URL, configurable from the Settings screen and
 * persisted so it survives a reload. There's no build-time env config here on
 * purpose: this is a PWA installed on a phone, pointed at whatever host is
 * running the FastAPI backend (a laptop on the same network, a Fly.io
 * deployment, etc.) — that has to be settable at runtime, not baked in.
 */

const STORAGE_KEY = "athlete-tracker:backend-url";
const DEFAULT_BACKEND_URL = "http://localhost:8000";

export function getBackendUrl(): string {
  try {
    return localStorage.getItem(STORAGE_KEY) ?? DEFAULT_BACKEND_URL;
  } catch {
    return DEFAULT_BACKEND_URL;
  }
}

export function setBackendUrl(url: string): void {
  const trimmed = url.trim().replace(/\/+$/, "");
  localStorage.setItem(STORAGE_KEY, trimmed || DEFAULT_BACKEND_URL);
}
