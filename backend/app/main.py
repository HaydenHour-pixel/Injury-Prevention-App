from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import days, nutrition, recovery, sleep, symptoms, training

app = FastAPI(title="Athlete Tracker API")

# The frontend (Vite dev server, or the installed PWA hitting whatever host is
# running this backend) is always a different origin from this API. There's
# no auth and no cookies (CLAUDE.md: single user, no auth system), so an open
# CORS policy doesn't expose anything a request couldn't already do directly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
