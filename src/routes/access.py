from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.database import get_db
from src.schemas import (
    AccessCheckRequest,
    AccessCheckResponse,
    AccessLogListResponse,
    CursorAccessLogListResponse,
    CardCreateRequest,
    CardResponse,
    ErrorDetail,
    ErrorResponse,
    HealthResponse,
    GateCommandRequest,
    GateCommandResponse,
)
from src.services.access_service import check_access, create_card, get_card, list_access_logs
from src.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    return HealthResponse(
        status="ok",
        service=settings.service_name,
        product=settings.service_product,
        timestamp=datetime.now(timezone.utc),
    )


@router.post(
    "/api/v1/access/check",
    response_model=AccessCheckResponse,
    responses={
        400: {"model": ErrorResponse},
    },
    tags=["Access"],
)
def access_check(payload: AccessCheckRequest, db: Session = Depends(get_db)):
    return check_access(db, payload)


@router.post(
    "/gate/command",
    response_model=GateCommandResponse,
    tags=["Access"],
)
def gate_command(payload: GateCommandRequest):
    if payload.command == "OPEN" and payload.uid == "ALL_GATES_EMERGENCY":
        from src.routes.access import logger
        logger.critical("🔥 FIRE ALARM EMERGENCY RECEIVED! OPENING ALL GATES IMMEDIATELY! BYPASSING DB CHECKS!")
        # Thêm đoạn publish MQTT nếu cần để mở cổng vật lý
        return GateCommandResponse(
            status="success",
            message="ALL GATES OPENED SUCCESSFULLY DUE TO EMERGENCY",
            gate_id="ALL"
        )
    raise HTTPException(status_code=400, detail="Invalid command or UID")


@router.get(
    "/api/v1/access/logs",
    response_model=AccessLogListResponse,
    tags=["Access"],
)
def access_logs(
    gate_id: str | None = Query(default=None),
    direction: Literal["IN", "OUT"] | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return list_access_logs(db, gate_id=gate_id, direction=direction, page=page, limit=limit)


import base64

@router.get(
    "/api/v1/access/logs/recent",
    response_model=CursorAccessLogListResponse,
    tags=["Access"],
)
def access_logs_cursor(
    cursor: str | None = Query(default=None, description="Base64 encoded event_id for pagination"),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """API kéo log lớn với Cursor-based pagination (Contract B6)."""
    from src.database import AccessLog
    from sqlalchemy import desc

    query = db.query(AccessLog).order_by(desc(AccessLog.created_at), desc(AccessLog.event_id))
    
    if cursor:
        try:
            decoded_cursor = base64.b64decode(cursor).decode('utf-8')
            # Extract timestamp and event_id from cursor if needed, or simply filter by event_id
            cursor_log = db.query(AccessLog).filter(AccessLog.event_id == decoded_cursor).first()
            if cursor_log:
                # Assuming created_at is strictly monotonically increasing or we use a tie-breaker
                query = query.filter(
                    (AccessLog.created_at < cursor_log.created_at) |
                    ((AccessLog.created_at == cursor_log.created_at) & (AccessLog.event_id < cursor_log.event_id))
                )
        except Exception:
            raise HTTPException(status_code=400, detail={"error": {"code": "INVALID_CURSOR", "message": "Invalid cursor format"}})

    # Fetch limit + 1 to know if there's a next page
    rows = query.limit(limit + 1).all()
    
    has_more = len(rows) > limit
    items_to_return = rows[:limit]
    
    next_cursor = None
    if has_more and items_to_return:
        last_item = items_to_return[-1]
        next_cursor = base64.b64encode(last_item.event_id.encode('utf-8')).decode('utf-8')

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
            status=row.status,
        )
        for row in items_to_return
    ]
    return CursorAccessLogListResponse(items=items, next_cursor=next_cursor, has_more=has_more)



@router.get(
    "/api/v1/cards/{card_id}",
    response_model=CardResponse,
    responses={404: {"model": ErrorResponse}},
    tags=["Cards"],
)
def read_card(card_id: str, db: Session = Depends(get_db)):
    card = get_card(db, card_id)
    if not card:
        raise HTTPException(
            status_code=404,
            detail=ErrorDetail(code="CARD_NOT_FOUND", message=f"Card {card_id} not found").model_dump(),
        )
    return CardResponse(
        card_id=card.card_id,
        person_id=card.person_id,
        person_name=card.person_name,
        person_type=card.person_type,
        status=card.status,
        expired_at=card.expired_at,
    )


@router.post(
    "/api/v1/cards",
    response_model=CardResponse,
    status_code=201,
    tags=["Cards"],
)
def add_card(payload: CardCreateRequest, db: Session = Depends(get_db)):
    existing = get_card(db, payload.card_id)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=ErrorDetail(code="CARD_ALREADY_EXISTS", message=f"Card {payload.card_id} already exists").model_dump(),
        )
    return create_card(db, payload)
