import logging
import time

from mini_soar.core.events import EventType, SOAREvent
from mini_soar.services.audit_service import AuditService
from mini_soar.services.docker_service import DockerService
from mini_soar.services.remediation_guard import RemediationGuard
from mini_soar.services.remediation_notifier import RemediationNotifier


logger = logging.getLogger("mini-soar")


docker_service = DockerService()
audit_service = AuditService()

remediation_guard = RemediationGuard(
    cooldown_seconds=60,
    event_ttl_seconds=600,
)

notifier = RemediationNotifier()


def handle_container_recovery(event: SOAREvent):
    started_at = time.monotonic()
    container = event.service

    # ==========================================================
    # Validate service/container
    # ==========================================================
    if not container:
        logger.error(
            "[REMEDIATION] Missing container name | event_id=%s",
            event.event_id,
        )
        return

    # ==========================================================
    # Remediation Guard
    # ==========================================================
    guard = remediation_guard.try_acquire(
        container=container,
        event_id=str(event.event_id),
    )

    if not guard.allowed:
        duration = time.monotonic() - started_at

        logger.warning(
            "[REMEDIATION SKIPPED] container=%s "
            "event_id=%s reason=%s",
            container,
            event.event_id,
            guard.reason,
        )

        audit_service.write(
            event_id=str(event.event_id),
            event_type=event.event_type.value,
            host=event.host,
            service=container,
            action="none",
            status="SKIPPED",
            duration_seconds=duration,
            message=guard.reason,
        )

        # Intentionally do NOT notify SKIPPED events.
        # This prevents duplicate/cooldown events from
        # creating notification noise.
        return

    remediation_success = False
    action = "none"
    audit_status = "FAILED"
    audit_message = ""

    logger.warning(
        "[REMEDIATION] Container recovery started | "
        "event_type=%s container=%s event_id=%s",
        event.event_type.value,
        container,
        event.event_id,
    )

    try:
        # ======================================================
        # Collect evidence before remediation
        # ======================================================
        logs = docker_service.collect_logs(container)

        logger.info(
            "[EVIDENCE] Last container logs | container=%s\n%s",
            container,
            logs[-3000:],
        )

        # ======================================================
        # CONTAINER_DOWN
        # ======================================================
        if event.event_type == EventType.CONTAINER_DOWN:
            action = "start"

            if docker_service.is_running(container):
                action = "none"

                logger.info(
                    "[REMEDIATION] Container already running | "
                    "container=%s",
                    container,
                )

            else:
                result = docker_service.start(container)

                logger.info(
                    "[REMEDIATION] action=%s success=%s message=%s",
                    result.action,
                    result.success,
                    result.message,
                )

                if not result.success:
                    audit_status = "FAILED"
                    audit_message = result.message
                    return

        # ======================================================
        # CONTAINER_UNHEALTHY
        # ======================================================
        elif event.event_type == EventType.CONTAINER_UNHEALTHY:
            if docker_service.is_running(container):
                action = "restart"
                result = docker_service.restart(container)

            else:
                action = "start"
                result = docker_service.start(container)

            logger.info(
                "[REMEDIATION] action=%s success=%s message=%s",
                result.action,
                result.success,
                result.message,
            )

            if not result.success:
                audit_status = "FAILED"
                audit_message = result.message
                return

        # ======================================================
        # Unsupported event
        # ======================================================
        else:
            audit_status = "FAILED"

            audit_message = (
                f"Unsupported event type: {event.event_type.value}"
            )

            logger.warning(
                "[REMEDIATION] Unsupported event type | "
                "event_type=%s",
                event.event_type.value,
            )

            return

        # ======================================================
        # Verification
        # ======================================================
        healthy = docker_service.wait_until_healthy(
            container,
            timeout=90,
            interval=5,
        )

        if healthy:
            remediation_success = True
            audit_status = "SUCCESS"
            audit_message = (
                "Container recovered and verified healthy"
            )

            logger.warning(
                "[REMEDIATION SUCCESS] "
                "container=%s event_id=%s",
                container,
                event.event_id,
            )

        else:
            audit_status = "FAILED"
            audit_message = (
                "Container failed health verification"
            )

            logger.error(
                "[REMEDIATION FAILED] "
                "container=%s event_id=%s",
                container,
                event.event_id,
            )

    except Exception as exc:
        audit_status = "ERROR"
        audit_message = str(exc)

        logger.exception(
            "[REMEDIATION ERROR] "
            "container=%s event_id=%s",
            container,
            event.event_id,
        )

    finally:
        # ======================================================
        # Release guard
        # ======================================================
        remediation_guard.release(
            container=container,
            success=remediation_success,
        )

        duration = time.monotonic() - started_at

        # ======================================================
        # Audit first
        # ======================================================
        audit_service.write(
            event_id=str(event.event_id),
            event_type=event.event_type.value,
            host=event.host,
            service=container,
            action=action,
            status=audit_status,
            duration_seconds=duration,
            message=audit_message,
        )

        logger.info(
            "[AUDIT] event_id=%s status=%s action=%s",
            event.event_id,
            audit_status,
            action,
        )

        # ======================================================
        # Notification second
        #
        # RemediationNotifier is fail-safe:
        # Discord failure must not change remediation outcome.
        # ======================================================
        if audit_status in {
            "SUCCESS",
            "FAILED",
            "ERROR",
        }:
            notifier.notify(
                event_id=str(event.event_id),
                event_type=event.event_type.value,
                host=event.host,
                service=container,
                action=action,
                status=audit_status,
                duration_seconds=duration,
                message=audit_message,
            )

        logger.info(
            "[REMEDIATION] Lock released | "
            "container=%s success=%s",
            container,
            remediation_success,
        )
