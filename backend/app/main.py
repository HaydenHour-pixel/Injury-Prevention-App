from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import days, nutrition, recovery, sleep, symptoms, training
from app.config import CORS_ORIGINS

app = FastAPI(title="Athlete Tracker API")

# The frontend (Vite dev server, or the installed PWA hitting whatever host is
# running this backend) is always a different origin from this API. Locked to
# an explicit allow-list (app/config.py) rather than "*" — there's no auth to
# protect, but an explicit list is still the right default and costs nothing.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(days.router, prefix="/api")
app.include_router(training.router, prefix="/api")
app.include_router(sleep.router, prefix="/api")
app.include_router(nutrition.router, prefix="/api")
app.include_router(recovery.router, prefix="/api")
app.include_router(symptoms.router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# Serves the built frontend (frontend/dist). Registered last, after every
# /api router and /health, so those still win on an exact match — routes are
# tried in registration order.
#
# Guarded on the directory actually existing: `npm run build` has to run
# first, and backend tests (this module gets imported by TestClient) must
# still work from a checkout where it hasn't been built yet.
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if FRONTEND_DIST.is_dir():
    # The hashed, cacheable build output (JS/CSS) — StaticFiles handles
    # Content-Type, ETags, and Range requests properly for these.
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="frontend-assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str) -> FileResponse:
        """Everything else: a real file on disk (icons, manifest.webmanifest,
        sw.js) if one exists at that path, otherwise index.html.

        That fallback is what makes the frontend's own pushState/popstate
        router (/day/2026-09-10, /settings) work on a hard reload or a direct
        link instead of 404ing — StaticFiles' `html=True` looked like it should
        provide this, but it only serves index.html for a directory path or a
        404.html on a miss; it has no SPA catch-all for arbitrary unmatched
        paths (verified against the installed starlette==0.41.3 source).

        `api/` is excluded so a genuinely bad API path still 404s instead of
        silently getting the SPA shell — this route is reached at all only
        when nothing registered above it (including every /api/* router)
        already matched, but a *mistyped* /api/ path would otherwise fall
        through to here rather than to a real 404.
        """
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404)
        candidate = FRONTEND_DIST / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
