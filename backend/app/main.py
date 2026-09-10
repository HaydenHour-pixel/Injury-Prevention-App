from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
