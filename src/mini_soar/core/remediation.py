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

class RemediationSummary(BaseModel):
    total: int
    success: int
    failed: int
    error: int
    skipped: int
    success_rate: float
    average_duration_seconds: float
class RemediationDistribution(BaseModel):
    status: dict[str, int]
    event_type: dict[str, int]
