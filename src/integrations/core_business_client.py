import hashlib
import logging

import httpx

from src.config import settings
from src.schemas import CoreBusinessAccessEvent

logger = logging.getLogger(__name__)


def send_to_core_business(event: CoreBusinessAccessEvent) -> None:
    """Gửi access event sang Core Business (B6)."""
    base_url = settings.core_business_url.rstrip("/")
    path = settings.core_business_event_path
    url = f"{base_url}{path}"

    # Generate Idempotency-Key: SHA256(StudentID + DeviceID + RoundToMinute(Timestamp))
    person_id = event.person_id or "UNKNOWN"
    gate_id = event.gate_id
    # Round timestamp to minute
    minute_timestamp = event.timestamp.replace(second=0, microsecond=0).isoformat()
    raw_key = f"{person_id}_{gate_id}_{minute_timestamp}"
    idempotency_key = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    headers = {
        "Idempotency-Key": idempotency_key,
        "Content-Type": "application/json"
    }

    # B6 chỉ nhận 3 field: gateId (camelCase), uid, timestamp (ISO 8601 với Z suffix)
    ts = event.timestamp
    # Chuẩn hóa timestamp sang format: 2026-06-17T09:08:42.511Z
    ts_str = ts.strftime("%Y-%m-%dT%H:%M:%S.") + f"{ts.microsecond // 1000:03d}Z"
    b6_payload = {
        "gateId": event.gate_id,
        "uid": event.card_id,
        "timestamp": ts_str,
    }

    try:
        with httpx.Client(timeout=settings.integration_timeout_seconds) as client:
            response = client.post(url, json=b6_payload, headers=headers)
            response.raise_for_status()
        logger.info("INTEGRATION core_business=success event_id=%s url=%s", event.event_id, url)
    except Exception as exc:
        logger.error(
            "INTEGRATION core_business=failed event_id=%s url=%s error=%s",
            event.event_id,
            url,
            exc,
        )
        # Store for bulk sync
        from src.services.offline import store_pending_event
        store_pending_event(event)
