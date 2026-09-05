import json
import logging
import os
from dataclasses import dataclass
from urllib import error, request

from dotenv import load_dotenv


load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class NotificationResult:
    success: bool
    message: str


class NotificationService:
    def __init__(self) -> None:
        self.enabled = (
            os.getenv("NOTIFICATIONS_ENABLED", "false")
            .strip()
            .lower()
            == "true"
        )

        self.discord_webhook_url = os.getenv(
            "DISCORD_WEBHOOK_URL",
            "",
        ).strip()

    def is_configured(self) -> bool:
        return bool(self.discord_webhook_url)

    def send_remediation_notification(
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
    ) -> NotificationResult:
        if not self.enabled:
            return NotificationResult(
                success=False,
                message="notifications_disabled",
            )
        if not self.should_notify(status):
            return NotificationResult(
                success=False,
                message="status_not_notifiable",
            )

        if not self.is_configured():
            logger.warning(
                "[NOTIFICATION] Discord webhook is not configured"
            )

            return NotificationResult(
                success=False,
                message="discord_webhook_not_configured",
            )

        payload = self._build_discord_payload(
            event_id=event_id,
            event_type=event_type,
            host=host,
            service=service,
            action=action,
            status=status,
            duration_seconds=duration_seconds,
            message=message,
        )

        body = json.dumps(payload).encode("utf-8")

        http_request = request.Request(
            self.discord_webhook_url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mini-SOAR/1.0",
            },
            method="POST",
        )

        try:
            with request.urlopen(
                http_request,
                timeout=5,
            ) as response:
                status_code = response.getcode()

            if 200 <= status_code < 300:
                logger.info(
                    "[NOTIFICATION] Discord notification sent "
                    "event_id=%s status=%s",
                    event_id,
                    status,
                )

                return NotificationResult(
                    success=True,
                    message="notification_sent",
                )

            logger.warning(
                "[NOTIFICATION] Discord returned HTTP %s",
                status_code,
            )

            return NotificationResult(
                success=False,
                message=f"http_{status_code}",
            )

        except error.HTTPError as exc:
            logger.exception(
                "[NOTIFICATION] Discord HTTP error: %s",
                exc.code,
            )

            return NotificationResult(
                success=False,
                message=f"http_error_{exc.code}",
            )

        except error.URLError as exc:
            logger.exception(
                "[NOTIFICATION] Discord connection error: %s",
                exc.reason,
            )

            return NotificationResult(
                success=False,
                message="connection_error",
            )

        except Exception:
            logger.exception(
                "[NOTIFICATION] Unexpected notification error"
            )

            return NotificationResult(
                success=False,
                message="unexpected_error",
            )

    @staticmethod
    def _build_discord_payload(
        *,
        event_id: str,
        event_type: str,
        host: str,
        service: str,
        action: str,
        status: str,
        duration_seconds: float,
        message: str | None,
    ) -> dict:
        color_map = {
            "SUCCESS": 5763719,
            "FAILED": 15548997,
            "ERROR": 15548997,
            "SKIPPED": 16705372,
        }

        color = color_map.get(
            status.upper(),
            5793266,
        )

        fields = [
            {
                "name": "Event",
                "value": event_type,
                "inline": True,
            },
            {
                "name": "Service",
                "value": service,
                "inline": True,
            },
            {
                "name": "Status",
                "value": status,
                "inline": True,
            },
            {
                "name": "Action",
                "value": action,
                "inline": True,
            },
            {
                "name": "Host",
                "value": host,
                "inline": True,
            },
            {
                "name": "Duration",
                "value": f"{duration_seconds:.3f}s",
                "inline": True,
            },
        ]

        if message:
            fields.append(
                {
                    "name": "Details",
                    "value": message[:1000],
                    "inline": False,
                }
            )

        return {
            "username": "Mini-SOAR",
            "embeds": [
                {
                    "title": f"Mini-SOAR Remediation: {status}",
                    "description": (
                        f"Security automation event `{event_id}` "
                        f"has completed."
                    ),
                    "color": color,
                    "fields": fields,
                    "footer": {
                        "text": "Mini-SOAR Security Automation"
                    },
                }
            ],
        }
    @staticmethod
    def should_notify(status: str) -> bool:
        return status.upper() in {
            "SUCCESS",
            "FAILED",
            "ERROR",
        }
