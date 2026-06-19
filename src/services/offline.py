import json
import logging
from typing import Any

from src.database import PendingEvent, SessionLocal
from src.schemas import CoreBusinessAccessEvent

logger = logging.getLogger(__name__)

# In-memory whitelist (loaded on startup)
_whitelist_cache: set[str] = set()

def load_whitelist() -> None:
    """Load all active cards into memory."""
    try:
        from src.database import Card
        with SessionLocal() as db:
            active_cards = db.query(Card.card_id).filter(Card.status == "active").all()
            _whitelist_cache.clear()
            for (card_id,) in active_cards:
                _whitelist_cache.add(card_id)
        logger.info("Loaded %d active cards into offline whitelist cache.", len(_whitelist_cache))
    except Exception as e:
        logger.error("Failed to load whitelist: %s", e)

def is_card_whitelisted(card_id: str) -> bool:
    """Check if card is in whitelist cache."""
    return card_id in _whitelist_cache

def store_pending_event(event: CoreBusinessAccessEvent) -> None:
    """Store event to DB when B6 is offline."""
    try:
        with SessionLocal() as db:
            payload = event.model_dump_json()
            pending = PendingEvent(payload=payload)
            db.add(pending)
            db.commit()
            logger.info("STORED pending_event for offline sync: event_id=%s", event.event_id)
    except Exception as e:
        logger.error("Failed to store pending event: %s", e)
