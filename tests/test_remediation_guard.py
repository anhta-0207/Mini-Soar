import unittest
from unittest.mock import patch

from mini_soar.services.remediation_guard import RemediationGuard


class RemediationGuardTest(unittest.TestCase):
    def test_first_event_is_allowed_and_second_is_duplicate(self):
        guard = RemediationGuard(
            cooldown_seconds=60,
            event_ttl_seconds=600,
        )

        first = guard.try_acquire("demo-web", "1125")
        duplicate = guard.try_acquire("demo-web", "1125")

        self.assertTrue(first.allowed)
        self.assertEqual(first.reason, "acquired")
        self.assertFalse(duplicate.allowed)
        self.assertEqual(duplicate.reason, "duplicate_event")

    def test_different_event_is_blocked_while_remediation_is_running(self):
        guard = RemediationGuard(
            cooldown_seconds=60,
            event_ttl_seconds=600,
        )

        first = guard.try_acquire("demo-web", "1125")
        blocked = guard.try_acquire("demo-web", "1126")

        self.assertTrue(first.allowed)
        self.assertFalse(blocked.allowed)
        self.assertEqual(blocked.reason, "remediation_in_progress")

        guard.release("demo-web", success=False)
        retry = guard.try_acquire("demo-web", "1126")

        self.assertTrue(retry.allowed)
        self.assertEqual(retry.reason, "acquired")

    def test_different_event_is_blocked_during_cooldown(self):
        guard = RemediationGuard(
            cooldown_seconds=60,
            event_ttl_seconds=600,
        )

        with patch(
            "mini_soar.services.remediation_guard.time.monotonic",
            return_value=100.0,
        ):
            first = guard.try_acquire("demo-web", "1125")
            guard.release("demo-web", success=True)

        with patch(
            "mini_soar.services.remediation_guard.time.monotonic",
            return_value=101.0,
        ):
            blocked = guard.try_acquire("demo-web", "1126")

        self.assertTrue(first.allowed)
        self.assertFalse(blocked.allowed)
        self.assertEqual(blocked.reason, "cooldown_active:59s")

        with patch(
            "mini_soar.services.remediation_guard.time.monotonic",
            return_value=161.0,
        ):
            retry = guard.try_acquire("demo-web", "1126")

        self.assertTrue(retry.allowed)
        self.assertEqual(retry.reason, "acquired")


if __name__ == "__main__":
    unittest.main()
