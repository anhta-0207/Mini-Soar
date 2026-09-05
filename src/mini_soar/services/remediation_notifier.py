import logging

from mini_soar.services.notification_service import NotificationService


logger = logging.getLogger(__name__)


class RemediationNotifier:
    def __init__(
        self,
        notification_service: NotificationService | None = None,
    ) -> None:
        self.notification_service = (
            notification_service
            or NotificationService()
        )

    def notify(
        self,
        *,
        event_id: str,
        event_type: str,
        host: str,
        service: str,
        action: str,
        status: str,
        duration_seconds: float,
        message: str | None = None,
    ) -> None:
        """
        Send a remediation notification.

        Notification failures must never propagate
        back into the remediation pipeline.
        """

        try:
            result = (
                self.notification_service
                .send_remediation_notification(
                    event_id=event_id,
                    event_type=event_type,
                    host=host,
                    service=service,
                    action=action,
                    status=status,
                    duration_seconds=duration_seconds,
                    message=message,
                )
            )

            if result.success:
                logger.info(
                    "[NOTIFICATION] sent "
                    "event_id=%s status=%s",
                    event_id,
                    status,
                )
            else:
                logger.info(
                    "[NOTIFICATION] skipped/failed "
                    "event_id=%s status=%s reason=%s",
                    event_id,
                    status,
                    result.message,
                )

        except Exception:
            logger.exception(
                "[NOTIFICATION] unexpected notifier error "
                "event_id=%s status=%s",
                event_id,
                status,
            )
