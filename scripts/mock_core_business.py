"""Mock Core Business (B6) — chạy port 3006 để test integration."""

from fastapi import FastAPI, Request
import uvicorn

app = FastAPI(title="Mock Core Business B6")


@app.get("/health")
def health():
    return {"status": "ok", "service": "mock-core-business-b6"}


from typing import Union

@app.post("/api/v1/events/access")
def receive_access_event(payload: Union[dict, list[dict]], request: Request):
    idempotency_key = request.headers.get("Idempotency-Key")
    print(f"[B6 MOCK] Idempotency-Key: {idempotency_key}")
    
    if isinstance(payload, list):
        print(f"[B6 MOCK] received BULK access events: {len(payload)} items")
        return {
            "received": True,
            "processed_count": len(payload),
        }
    else:
        print("[B6 MOCK] received single access event:", payload)
        return {
            "received": True,
            "event_id": payload.get("event_id"),
            "policy_result": "NORMAL",
            "alert_required": False,
        }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3006)
