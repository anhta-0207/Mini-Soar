from enum import Enum

from pydantic import BaseModel, Field


class EventType(str, Enum):
    HIGH_CPU = "HIGH_CPU"
    CONTAINER_DOWN = "CONTAINER_DOWN"
    CONTAINER_UNHEALTHY = "CONTAINER_UNHEALTHY"
    UNKNOWN = "UNKNOWN"


class EventState(str, Enum):
    PROBLEM = "PROBLEM"
    RECOVERY = "RECOVERY"


class ZabbixTag(BaseModel):
    tag: str
    value: str


class ZabbixEvent(BaseModel):
    source: str = "zabbix"

    event_id: str
    event_name: str

    event_value: int
    severity: str

    host: str
    trigger_id: str

    tags: list[ZabbixTag] = Field(default_factory=list)


class SOAREvent(BaseModel):
    event_id: str
    event_type: EventType
    state: EventState

    host: str
    service: str | None = None
    severity: str

    original_event: ZabbixEvent
