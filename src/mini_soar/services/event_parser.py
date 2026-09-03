from mini_soar.core.events import (
    EventState,
    EventType,
    SOAREvent,
    ZabbixEvent,
)


def parse_zabbix_event(event: ZabbixEvent) -> SOAREvent:
    tags = {
        item.tag: item.value
        for item in event.tags
    }

    raw_event_type = tags.get("event_type", "UNKNOWN")

    try:
        event_type = EventType(raw_event_type)
    except ValueError:
        event_type = EventType.UNKNOWN

    state = (
        EventState.PROBLEM
        if event.event_value == 1
        else EventState.RECOVERY
    )

    return SOAREvent(
        event_id=event.event_id,
        event_type=event_type,
        state=state,
        host=event.host,
        service=tags.get("service"),
        severity=event.severity,
        original_event=event,
    )
