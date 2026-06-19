from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: list[str] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    error: ErrorDetail


class HealthResponse(BaseModel):
    status: str
    service: str
    product: str
    timestamp: datetime


class AccessCheckRequest(BaseModel):
    card_id: str = Field(..., min_length=1, examples=["RFID-2026-001"])
    gate_id: str = Field(..., min_length=1, examples=["gate-main"])
    direction: Literal["IN", "OUT"]
    timestamp: datetime


class AccessCheckResponse(BaseModel):
    access_granted: bool
    reason: str
    person_id: Optional[str] = None
    person_name: Optional[str] = None
    person_type: Optional[str] = None
    gate_id: str
    direction: Literal["IN", "OUT"]
    event_id: str
    checked_at: datetime


class CardCreateRequest(BaseModel):
    card_id: str
    person_id: str
    person_name: str
    person_type: Literal["student", "staff", "guest"] = "student"
    status: Literal["active", "expired", "blocked"] = "active"


class CardResponse(BaseModel):
    card_id: str
    person_id: str
    person_name: str
    person_type: str
    status: str
    expired_at: Optional[datetime] = None


class AccessLogItem(BaseModel):
    event_id: str
    card_id: str
    person_id: Optional[str] = None
    person_name: Optional[str] = None
    person_type: Optional[str] = None
    gate_id: str
    direction: str
    access_granted: bool
    reason: str
    timestamp: datetime
    created_at: datetime
    status: str = "COMPLETED"


class AccessLogListResponse(BaseModel):
    items: list[AccessLogItem]
    total: int
    page: int
    limit: int


class CursorAccessLogListResponse(BaseModel):
    items: list[AccessLogItem]
    next_cursor: Optional[str] = None
    has_more: bool


class AccessCancelRequest(BaseModel):
    event_id: str
    reason: Literal["PHYSICAL_TIMEOUT_NO_PASSAGE"] = "PHYSICAL_TIMEOUT_NO_PASSAGE"


class AccessCancelResponse(BaseModel):
    event_id: str
    status: str
    message: str


class CoreBusinessAccessEvent(BaseModel):
    """Payload B3 gửi sang Core Business (B6) — cần thống nhất với nhóm B6."""

    event_id: str
    card_id: str
    person_id: Optional[str] = None
    person_name: Optional[str] = None
    person_type: Optional[str] = None
    gate_id: str
    direction: Literal["IN", "OUT"]
    access_granted: bool
    reason: str
    timestamp: datetime
    source_service: str
    product: str
    status: str = "COMPLETED"


class AnalyticsAccessEvent(BaseModel):
    """Payload B3 gửi sang Analytics (B5) — cần thống nhất với nhóm B5."""

    event_id: str
    gate_id: str
    direction: Literal["IN", "OUT"]
    access_granted: bool
    person_type: Optional[str] = None
    timestamp: datetime
    source_service: str
    product: str


class RawRFIDEvent(BaseModel):
    """Payload B3 nhận từ HiveMQ (Data RFID)."""
    event_id: str
    event_type: str
    source_service: str
    device_id: str
    timestamp: datetime
    uid: str
    door_id: str
    location: str
    direction: str


class ProcessedAccessEvent(BaseModel):
    """Payload B3 gửi ngược lại HiveMQ."""
    event_id: str
    event_type: str = "access.swipe.processed"
    source_service: str = "team-gate"
    timestamp: datetime
    raw_event_id: str
    uid: str
    student_id: Optional[str] = None
    full_name: Optional[str] = None
    class_name: Optional[str] = None
    door_id: str
    location: str
    direction: str
    access_result: Literal["granted", "denied"]
    reason: str
