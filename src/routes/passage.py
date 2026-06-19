from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import AccessLog, get_db
from src.integrations.core_business_client import send_to_core_business
from src.schemas import (
    AccessCancelRequest,
    AccessCancelResponse,
    CoreBusinessAccessEvent,
    ErrorDetail,
    ErrorResponse
)
from src.config import settings

router = APIRouter()

@router.post(
    "/api/v1/access/cancel",
    response_model=AccessCancelResponse,
    responses={404: {"model": ErrorResponse}},
    tags=["Access"],
)
def cancel_access(payload: AccessCancelRequest, db: Session = Depends(get_db)):
    """Physical Passage Timeout - cổng tự đóng do sinh viên không đi qua."""
    log = db.query(AccessLog).filter(AccessLog.event_id == payload.event_id).first()
    if not log:
        raise HTTPException(
            status_code=404,
            detail=ErrorDetail(code="EVENT_NOT_FOUND", message=f"Event {payload.event_id} not found").model_dump(),
        )

    if log.status == "CANCELLED":
        return AccessCancelResponse(
            event_id=log.event_id,
            status=log.status,
            message="Already cancelled"
        )

    log.status = "CANCELLED"
    db.commit()

    # Notify Core Business
    core_payload = CoreBusinessAccessEvent(
        event_id=log.event_id,
        card_id=log.card_id,
        person_id=log.person_id,
        person_name=log.person_name,
        person_type=log.person_type,
        gate_id=log.gate_id,
        direction=log.direction,
        access_granted=log.access_granted,
        reason=payload.reason,
        timestamp=log.timestamp,
        source_service=settings.service_name,
        product=settings.service_product,
        status="ACCESS_CANCELLED" # Explicit contract
    )
    send_to_core_business(core_payload)

    return AccessCancelResponse(
        event_id=log.event_id,
        status="CANCELLED",
        message="Access cancelled successfully"
    )
