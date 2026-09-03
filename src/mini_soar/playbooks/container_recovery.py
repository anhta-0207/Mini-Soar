import logging

from mini_soar.core.events import SOAREvent


logger = logging.getLogger("mini-soar")


def handle_container_recovery(event: SOAREvent) -> None:
    logger.warning(
        "[DRY-RUN] Container recovery playbook | "
        "event_type=%s host=%s service=%s event_id=%s",
        event.event_type.value,
        event.host,
        event.service,
        event.event_id,
    )

    logger.info(
        "[DRY-RUN] Would inspect container %s",
        event.service,
    )

    logger.info(
        "[DRY-RUN] Would collect container logs for %s",
        event.service,
    )

    logger.info(
        "[DRY-RUN] Would restart container %s",
        event.service,
    )

    logger.info(
        "[DRY-RUN] Would verify container health after remediation"
    )
