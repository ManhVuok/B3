import logging

import httpx

from src.config import settings
from src.schemas import AnalyticsAccessEvent

logger = logging.getLogger(__name__)


def send_to_analytics(event: AnalyticsAccessEvent) -> None:
    """Gửi access metric sang Analytics (B5)."""
    base_url = settings.analytics_url.rstrip("/")
    path = settings.analytics_ingest_path
    url = f"{base_url}{path}"

    try:
        with httpx.Client(timeout=settings.integration_timeout_seconds) as client:
            response = client.post(url, json=event.model_dump(mode="json"))
            response.raise_for_status()
        logger.info("INTEGRATION analytics=success event_id=%s url=%s", event.event_id, url)
    except Exception as exc:
        logger.error(
            "INTEGRATION analytics=failed event_id=%s url=%s error=%s",
            event.event_id,
            url,
            exc,
        )
