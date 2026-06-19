import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.config import settings
from src.database import AccessLog, Card, generate_event_id
from src.integrations.analytics_client import send_to_analytics
from src.integrations.core_business_client import send_to_core_business
from src.schemas import (
    AccessCheckRequest,
    AccessCheckResponse,
    AccessLogItem,
    AccessLogListResponse,
    AnalyticsAccessEvent,
    CardCreateRequest,
    CardResponse,
    CoreBusinessAccessEvent,
)

logger = logging.getLogger(__name__)


def _evaluate_card(card: Card | None) -> tuple[bool, str, Card | None]:
    if card is None:
        return False, "Unknown card", None

    if card.status == "active":
        if card.person_type == "student":
            return True, "Valid student card", card
        if card.person_type == "staff":
            return True, "Valid staff card", card
        return True, "Valid guest card", card

    if card.status == "expired":
        return False, "Card expired", card

    if card.status == "blocked":
        return False, "Card blocked", card

    return False, "Invalid card status", card


def check_access(db: Session, payload: AccessCheckRequest) -> AccessCheckResponse:
    from src.services.debounce import debounce
    from src.services.offline import is_card_whitelisted

    # 1. Debounce check
    if not debounce.check(payload.card_id):
        checked_at = datetime.now(timezone.utc)
        return AccessCheckResponse(
            access_granted=False,
            reason="Card debounce - please wait",
            gate_id=payload.gate_id,
            direction=payload.direction,
            event_id=generate_event_id(),
            checked_at=checked_at,
        )

    card = db.query(Card).filter(Card.card_id == payload.card_id).first()
    
    # 2. Offline Mode Whitelist fallback
    if card is None and settings.offline_mode == "fail_closed":
        if is_card_whitelisted(payload.card_id):
            # We don't have full info, but we know it's in the whitelist
            card = Card(card_id=payload.card_id, status="active", person_type="student")

    access_granted, reason, matched_card = _evaluate_card(card)
    checked_at = datetime.now(timezone.utc)

    log = AccessLog(
        event_id=generate_event_id(),
        card_id=payload.card_id,
        person_id=matched_card.person_id if matched_card else None,
        person_name=matched_card.person_name if matched_card else None,
        person_type=matched_card.person_type if matched_card else None,
        gate_id=payload.gate_id,
        direction=payload.direction,
        access_granted=access_granted,
        reason=reason,
        timestamp=payload.timestamp,
        created_at=checked_at,
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    logger.info(
        "ACCESS_CHECK card_id=%s granted=%s event_id=%s gate=%s direction=%s",
        payload.card_id,
        access_granted,
        log.event_id,
        payload.gate_id,
        payload.direction,
    )

    core_payload = CoreBusinessAccessEvent(
        event_id=log.event_id,
        card_id=log.card_id,
        person_id=log.person_id,
        person_name=log.person_name,
        person_type=log.person_type,
        gate_id=log.gate_id,
        direction=log.direction,
        access_granted=log.access_granted,
        reason=log.reason,
        timestamp=log.timestamp,
        source_service=settings.service_name,
        product=settings.service_product,
    )
    analytics_payload = AnalyticsAccessEvent(
        event_id=log.event_id,
        gate_id=log.gate_id,
        direction=log.direction,
        access_granted=log.access_granted,
        person_type=log.person_type,
        timestamp=log.timestamp,
        source_service=settings.service_name,
        product=settings.service_product,
    )

    send_to_core_business(core_payload)
    send_to_analytics(analytics_payload)

    return AccessCheckResponse(
        access_granted=log.access_granted,
        reason=log.reason,
        person_id=log.person_id,
        person_name=log.person_name,
        person_type=log.person_type,
        gate_id=log.gate_id,
        direction=log.direction,
        event_id=log.event_id,
        checked_at=checked_at,
    )


def list_access_logs(
    db: Session,
    *,
    gate_id: str | None = None,
    direction: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> AccessLogListResponse:
    query = db.query(AccessLog)
    if gate_id:
        query = query.filter(AccessLog.gate_id == gate_id)
    if direction:
        query = query.filter(AccessLog.direction == direction)

    total = query.count()
    rows = (
        query.order_by(AccessLog.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    items = [
        AccessLogItem(
            event_id=row.event_id,
            card_id=row.card_id,
            person_id=row.person_id,
            person_name=row.person_name,
            person_type=row.person_type,
            gate_id=row.gate_id,
            direction=row.direction,
            access_granted=row.access_granted,
            reason=row.reason,
            timestamp=row.timestamp,
            created_at=row.created_at,
        )
        for row in rows
    ]
    return AccessLogListResponse(items=items, total=total, page=page, limit=limit)


def get_card(db: Session, card_id: str) -> Card | None:
    return db.query(Card).filter(Card.card_id == card_id).first()


def create_card(db: Session, payload: CardCreateRequest) -> CardResponse:
    card = Card(
        card_id=payload.card_id,
        person_id=payload.person_id,
        person_name=payload.person_name,
        person_type=payload.person_type,
        status=payload.status,
        expired_at=None,
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    return CardResponse(
        card_id=card.card_id,
        person_id=card.person_id,
        person_name=card.person_name,
        person_type=card.person_type,
        status=card.status,
        expired_at=card.expired_at,
    )
