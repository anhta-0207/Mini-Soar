import logging

from mini_soar.core.events import SOAREvent


logger = logging.getLogger("mini-soar")


def handle_high_cpu(event: SOAREvent) -> None:
    logger.warning(
        "[DRY-RUN] HIGH_CPU playbook | "
        "host=%s service=%s event_id=%s",
        event.host,
        event.service,
        event.event_id,
    )

    logger.info(
        "[DRY-RUN] Would investigate high CPU usage on %s",
        event.service,
    )
