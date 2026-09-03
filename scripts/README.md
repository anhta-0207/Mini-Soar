# Controlled Failure Simulation

These scripts create repeatable failures for the isolated Mini-SOAR lab. They intentionally consume resources or disrupt `demo-web`; do not run them against production systems or shared workloads.

## Prerequisites

- Docker is installed and `demo-web` exists.
- The current account can operate the lab container.
- `demo-web` is exposed on `http://localhost:8000`.
- Zabbix Agent 2 is collecting the required Docker items.
- The `HIGH_CPU`, `CONTAINER_DOWN`, and `CONTAINER_UNHEALTHY` triggers and webhook action are enabled.
- Mini-SOAR is running on port `9000` when testing automated remediation.

Confirm the starting state:

```bash
docker ps --filter name=demo-web
curl -i http://localhost:8000/health
curl -i http://localhost:9000/health
```

## `container_down.sh`

### Purpose

Validate stopped-container detection and the `CONTAINER_DOWN` self-healing path.

### Usage

```bash
./scripts/container_down.sh
```

### Actual Behavior

The script runs `docker stop demo-web` and prints a reminder that Zabbix should detect `CONTAINER_DOWN`.

### Expected Result

1. Docker reports `demo-web` as stopped.
2. Zabbix creates a `CONTAINER_DOWN` problem.
3. The Zabbix Action posts the event to Mini-SOAR.
4. The remediation guard accepts the event.
5. Mini-SOAR runs `docker start demo-web` through `DockerService`.
6. The playbook waits for running and healthy state.
7. A `SUCCESS` record with `action=start` is written to JSONL and MariaDB.
8. Zabbix later emits a recovery event, which Mini-SOAR logs without another remediation.

Do not start the container manually during an end-to-end self-healing test. If Mini-SOAR is unavailable or remediation fails, recover the lab with:

```bash
docker start demo-web
```

## `container_unhealthy.sh`

### Purpose

Validate application-health detection and the `CONTAINER_UNHEALTHY` self-healing path.

### Usage

```bash
./scripts/container_unhealthy.sh
```

### Actual Behavior

The script sends an HTTP `POST` request to `http://localhost:8000/simulate/unhealthy`. The demo application sets an in-memory flag, causing subsequent `GET /health` requests to return HTTP `503` while the process continues running.

The script does not create a file in `/tmp`.

### Expected Result

1. The endpoint confirms that the fault was injected.
2. Docker health checks transition `demo-web` to `unhealthy` after the configured retries.
3. Zabbix creates a `CONTAINER_UNHEALTHY` problem and sends the webhook.
4. Mini-SOAR runs `docker restart demo-web` through `DockerService`.
5. Restarting resets the in-memory fault state.
6. The playbook verifies the recovered container.
7. A `SUCCESS` record with `action=restart` is written to JSONL and MariaDB.

## `container_unhealthy_recover.sh`

### Purpose

Clear the simulated unhealthy state without restarting the workload. This is useful when validating detection/recovery independently from automated remediation.

### Usage

```bash
./scripts/container_unhealthy_recover.sh
```

### Actual Behavior

The script sends an HTTP `POST` request to `http://localhost:8000/simulate/recover`, which resets the in-memory fault flag.

### Expected Result

`GET /health` returns HTTP `200`, Docker eventually reports `healthy`, and Zabbix creates a recovery event. During a full Mini-SOAR self-healing test this script is normally unnecessary because the automated restart resets the state.

## `cpu_spike.sh`

### Purpose

Validate sustained CPU monitoring and the `HIGH_CPU` investigation policy.

### Usage

```bash
./scripts/cpu_spike.sh
```

### Actual Behavior

The script starts a detached Python busy loop inside `demo-web`:

```text
python -c "while True: pass"
```

### Expected Result

1. Container CPU utilization rises.
2. Zabbix creates a `HIGH_CPU` event after its averaging window and action interval.
3. Mini-SOAR routes the event to the dry-run investigation playbook.
4. No automatic Docker restart occurs.

This non-remediation policy is intentional because high CPU alone is not sufficient evidence for a safe restart.

### Recovery

The current script does not track the detached process ID. After completing the test, restart the lab workload to stop the busy loop:

```bash
docker restart demo-web
```

Then wait for CPU usage and the Zabbix moving average to return below the trigger threshold.

## Observing Results

Watch Mini-SOAR logs for event routing, Docker actions, verification, and audit status. Query recent persisted records with:

```bash
curl -s "http://localhost:9000/api/v1/remediations?limit=10"
```

The local JSONL audit is written to `logs/remediation.jsonl`. Duplicate, in-progress, or cooldown decisions appear as `SKIPPED` records rather than Docker actions.
