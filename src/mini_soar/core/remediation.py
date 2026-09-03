from datetime import datetime

from pydantic import BaseModel


class RemediationRecord(BaseModel):
    id: int
    event_id: str
    event_type: str
    host: str
    service: str
    action: str
    status: str
    duration_seconds: float
    message: str | None = None
    created_at: datetime


class RemediationListResponse(BaseModel):
    count: int
    items: list[RemediationRecord]
