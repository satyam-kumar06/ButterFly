"""Phase 0 health endpoint only; journey routes are the Brain owner's Phase 1 work."""

from fastapi import FastAPI

app = FastAPI(title="Fork", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "phase": "0", "mode": "foundation"}
