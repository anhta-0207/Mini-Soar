import logging
import threading
import time
from dataclasses import dataclass

logger = logging.getLogger("mini-soar")


@dataclass
class GuardResult:
    allowed: bool
    reason: str


class RemediationGuard:
    def __init__(
        self,
        cooldown_seconds: int = 60,
        event_ttl_seconds: int = 600,
    ):
        self.cooldown_seconds = cooldown_seconds
        self.event_ttl_seconds = event_ttl_seconds

        self._lock = threading.Lock()

        # Container currently being remediated
        self._in_progress: set[str] = set()

        # Last successful remediation time
        self._last_success: dict[str, float] = {}

        # event_id -> timestamp
        self._seen_events: dict[str, float] = {}

    def _cleanup_seen_events(self) -> None:
        now = time.monotonic()

        expired = [
            event_id
            for event_id, timestamp in self._seen_events.items()
            if now - timestamp > self.event_ttl_seconds
        ]

        for event_id in expired:
            del self._seen_events[event_id]

    def try_acquire(
        self,
        container: str,
        event_id: str,
    ) -> GuardResult:

        with self._lock:
            now = time.monotonic()

            self._cleanup_seen_events()

            # 1. Duplicate event
            if event_id in self._seen_events:
                return GuardResult(
                    allowed=False,
                    reason="duplicate_event",
                )

            self._seen_events[event_id] = now

            # 2. Another remediation is already running
            if container in self._in_progress:
                return GuardResult(
                    allowed=False,
                    reason="remediation_in_progress",
                )

            # 3. Cooldown
            last_success = self._last_success.get(container)

            if last_success is not None:
                remaining = self.cooldown_seconds - (
                    now - last_success
                )

                if remaining > 0:
                    return GuardResult(
                        allowed=False,
                        reason=f"cooldown_active:{remaining:.0f}s",
                    )

            self._in_progress.add(container)

            return GuardResult(
                allowed=True,
                reason="acquired",
            )

    def release(
        self,
        container: str,
        success: bool,
    ) -> None:

        with self._lock:
            self._in_progress.discard(container)

            if success:
                self._last_success[container] = time.monotonic()
