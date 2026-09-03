import logging

from mini_soar.core.events import EventState, EventType, SOAREvent
from mini_soar.playbooks.container_recovery import (
    handle_container_recovery,
)
from mini_soar.playbooks.high_cpu import handle_high_cpu


logger = logging.getLogger("mini-soar")


def route_event(event: SOAREvent) -> None:
    if event.state == EventState.RECOVERY:
        logger.info(
            "Recovery event received | "
            "event_type=%s service=%s event_id=%s",
            event.event_type.value,
            event.service,
            event.event_id,
        )
        return

    if event.event_type == EventType.HIGH_CPU:
        handle_high_cpu(event)
        return

    if event.event_type in (
        EventType.CONTAINER_DOWN,
        EventType.CONTAINER_UNHEALTHY,
    ):
        handle_container_recovery(event)
        return

    logger.warning(
        "No playbook available | event_type=%s event_id=%s",
        event.event_type.value,
        event.event_id,
    )
