import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from mini_soar.services.database_service import DatabaseService

logger = logging.getLogger("mini-soar")


class AuditService:
    def __init__(self, log_path: str = "logs/remediation.jsonl"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self.database = DatabaseService()

    def write(
        self,
        *,
        event_id: str,
        event_type: str,
        host: str,
        service: str,
        action: str,
        status: str,
        duration_seconds: float,
        message: str = "",
    ) -> None:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_id": event_id,
            "event_type": event_type,
            "host": host,
            "service": service,
            "action": action,
            "status": status,
            "duration_seconds": round(duration_seconds, 3),
            "message": message,
        }

        line = json.dumps(record, ensure_ascii=False)

        with self._lock:
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
        try:
            self.database.insert_remediation(
            event_id=event_id,
            event_type=event_type,
            host=host,
            service=service,
            action=action,
            status=status,
            duration_seconds=duration_seconds,
            message=message,
        )

        except Exception:
    	    logger.exception(
    	        "[AUDIT] Database write failed | event_id=%s",
                event_id,
        )

        logger.info(
            "[AUDIT] event_id=%s action=%s status=%s duration=%.3fs",
            event_id,
            action,
            status,
            duration_seconds,
        )
