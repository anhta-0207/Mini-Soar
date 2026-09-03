import logging
import subprocess
import time
from dataclasses import dataclass

logger = logging.getLogger("mini-soar")


@dataclass
class RemediationResult:
    success: bool
    action: str
    container: str
    message: str


class DockerService:
    def __init__(self):
        self.allowed_containers = {"demo-web"}

    def _validate_container(self, container: str):
        if container not in self.allowed_containers:
            raise ValueError(
                f"Container '{container}' is not allowed for remediation"
            )

    def _run(self, args: list[str]) -> subprocess.CompletedProcess:
        logger.info("Executing command | command=%s", " ".join(args))

        return subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )

    def is_running(self, container: str) -> bool:
        self._validate_container(container)

        result = self._run([
            "docker",
            "inspect",
            "--format={{.State.Running}}",
            container,
        ])

        return result.returncode == 0 and result.stdout.strip() == "true"

    def health_status(self, container: str) -> str:
        self._validate_container(container)

        result = self._run([
            "docker",
            "inspect",
            "--format={{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}",
            container,
        ])

        if result.returncode != 0:
            return "unknown"

        return result.stdout.strip()

    def collect_logs(self, container: str, tail: int = 50) -> str:
        self._validate_container(container)

        result = self._run([
            "docker",
            "logs",
            "--tail",
            str(tail),
            container,
        ])

        return result.stdout + result.stderr

    def start(self, container: str) -> RemediationResult:
        self._validate_container(container)

        logger.warning(
            "[REMEDIATION] Starting container | container=%s",
            container,
        )

        result = self._run([
            "docker",
            "start",
            container,
        ])

        if result.returncode != 0:
            return RemediationResult(
                success=False,
                action="start",
                container=container,
                message=result.stderr.strip(),
            )

        return RemediationResult(
            success=True,
            action="start",
            container=container,
            message="Container started successfully",
        )

    def restart(self, container: str) -> RemediationResult:
        self._validate_container(container)

        logger.warning(
            "[REMEDIATION] Restarting container | container=%s",
            container,
        )

        result = self._run([
            "docker",
            "restart",
            container,
        ])

        if result.returncode != 0:
            return RemediationResult(
                success=False,
                action="restart",
                container=container,
                message=result.stderr.strip(),
            )

        return RemediationResult(
            success=True,
            action="restart",
            container=container,
            message="Container restarted successfully",
        )

    def wait_until_healthy(
        self,
        container: str,
        timeout: int = 60,
        interval: int = 5,
    ) -> bool:
        self._validate_container(container)

        deadline = time.time() + timeout

        while time.time() < deadline:
            running = self.is_running(container)
            health = self.health_status(container)

            logger.info(
                "[VERIFY] container=%s running=%s health=%s",
                container,
                running,
                health,
            )

            if running and health in {"healthy", "none"}:
                return True

            time.sleep(interval)

        return False
