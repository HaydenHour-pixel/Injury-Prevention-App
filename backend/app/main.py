from fastapi import FastAPI

from app.api import days, nutrition, recovery, sleep, symptoms, training

app = FastAPI(title="Athlete Tracker API")

app.include_router(days.router, prefix="/api")
app.include_router(training.router, prefix="/api")
app.include_router(sleep.router, prefix="/api")
app.include_router(nutrition.router, prefix="/api")
app.include_router(recovery.router, prefix="/api")
app.include_router(symptoms.router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
