from fastapi import FastAPI

app = FastAPI(title="Athlete Tracker API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
