import json
import logging
import time
import threading
from datetime import datetime, timezone

import httpx

from src.config import settings
from src.database import PendingEvent, SessionLocal

logger = logging.getLogger(__name__)

def sync_pending_events() -> None:
    """Read pending events and bulk sync to Core Business."""
    try:
        with SessionLocal() as db:
            pending = db.query(PendingEvent).filter(PendingEvent.synced == False).order_by(PendingEvent.created_at.asc()).limit(settings.bulk_sync_batch_size).all()
            
            if not pending:
                return

            base_url = settings.core_business_url.rstrip("/")
            path = settings.core_business_event_path
            url = f"{base_url}{path}"
            
            logger.info("BULK_SYNC attempting to send %d events to %s", len(pending), url)
            
            with httpx.Client(timeout=10.0) as client:
                for p in pending:
                    event_data = json.loads(p.payload)
                    # Convert to B6 format
                    ts_str = event_data.get("timestamp")
                    if ts_str and not ts_str.endswith("Z"):
                        # Attempt to format if necessary
                        if "+" in ts_str:
                            ts_str = ts_str.split("+")[0]
                        if "." not in ts_str:
                            ts_str += ".000"
                        ts_str += "Z"
                        
                    b6_payload = {
                        "gateId": event_data.get("gate_id"),
                        "uid": event_data.get("card_id"),
                        "timestamp": ts_str,
                    }
                    
                    try:
                        response = client.post(url, json=b6_payload)
                        response.raise_for_status()
                        p.synced = True
                        p.synced_at = datetime.now(timezone.utc)
                    except Exception as exc:
                        logger.warning("BULK_SYNC item failed: %s", exc)
                        break # Stop on first failure to keep order
                
            db.commit()
            logger.info("BULK_SYNC batch processed.")
            
    except Exception as e:
        logger.error("BULK_SYNC failed: %s", e)

def start_background_sync() -> None:
    """Start background thread to run bulk sync periodically."""
    def _run():
        while True:
            sync_pending_events()
            time.sleep(10) # Run every 10 seconds

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    logger.info("Background bulk sync thread started.")
