"""Mock Analytics (B5) — chạy port 3005 để test integration."""

from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Mock Analytics B5")


@app.get("/health")
def health():
    return {"status": "ok", "service": "mock-analytics-b5"}


@app.post("/api/v1/ingest/access")
def ingest_access_event(payload: dict):
    print("[B5 MOCK] received access metric:", payload)
    return {"received": True, "event_id": payload.get("event_id")}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3005)
