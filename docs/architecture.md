# Mini-SOAR Technical Architecture

## Scope and Status

Mini-SOAR is an isolated portfolio lab for event-driven monitoring and guarded self-healing. The repository currently implements infrastructure, detection, webhook ingestion, event routing, automated container recovery, verification, audit persistence, and remediation history APIs.

The design separates monitoring, decision, action, and evidence responsibilities. It is production-oriented in structure, but current runtime characteristics such as synchronous execution and in-memory guard state are appropriate for a single-node lab rather than a production control plane.

## System Context

```mermaid
flowchart LR
    subgraph Monitored_Host[Monitored host - 192.168.136.110]
        A[demo-web :8000]
        B[Docker daemon]
        C[Zabbix Agent 2]
        D[Mini-SOAR API :9000]
        A --> B
        B --> C
        D --> B
    end

    subgraph Monitoring[Zabbix server - 192.168.136.102]
        E[Items and discovery]
        F[Triggers]
        G[Action and webhook]
        E --> F --> G
    end

    C --> E
    G --> D
    D --> H[(MariaDB)]
    D --> I[JSONL audit]
    H --> J[Remediation history API]
```

The monitored host and Mini-SOAR engine currently share access to the local Docker daemon. That access is highly privileged and is a deliberate lab boundary.

## Mini-SOAR Internal Flow

```mermaid
flowchart TD
    A[POST /api/v1/webhooks/zabbix] --> B[ZabbixEvent validation]
    B --> C[Event Parser]
    C --> D[SOAREvent]
    D --> E{Event Router}
    E -->|RECOVERY| F[Log and stop]
    E -->|HIGH_CPU PROBLEM| G[Investigation-only playbook]
    E -->|Container PROBLEM| H[Remediation Guard]
    E -->|UNKNOWN| I[Warning and stop]
    H -->|Denied| J[SKIPPED audit]
    H -->|Allowed| K[Container recovery playbook]
    K --> L[Collect logs]
    L --> M[DockerService start or restart]
    M --> N[Running and health verification]
    N --> O[SUCCESS / FAILED / ERROR audit]
    J --> P[JSONL and MariaDB]
    O --> P
```

## Component Responsibilities

| Component | Responsibility |
|---|---|
| `app/main.py` | Runs the monitored `demo-web` workload, health endpoint, and lab-only unhealthy simulation endpoints |
| Zabbix Agent 2 | Collects host and Docker telemetry from the monitored server |
| Zabbix Server | Stores telemetry, evaluates triggers, creates events, and invokes the webhook action |
| `api/zabbix.py` | Validates webhook payloads, logs normalized event details, and invokes routing |
| `services/event_parser.py` | Converts `ZabbixEvent` into the internal `SOAREvent` model |
| `playbooks/router.py` | Applies state and event-type routing policy |
| `services/remediation_guard.py` | Enforces event deduplication, per-container in-progress state, and successful-remediation cooldown |
| `playbooks/container_recovery.py` | Orchestrates evidence collection, Docker action selection, verification, release, and audit |
| `playbooks/high_cpu.py` | Logs investigation-only behavior without restarting the workload |
| `services/docker_service.py` | Validates the container allowlist and runs fixed Docker CLI argument lists with timeouts |
| `services/audit_service.py` | Appends JSONL records and attempts MariaDB persistence |
| `services/database_service.py` | Executes parameterized MariaDB inserts and history queries |
| `api/remediations.py` | Exposes list/filter and event-ID lookup endpoints for remediation history |

## Package Boundaries

### `api/`

Owns HTTP transport concerns: request validation, query parameters, response models, and HTTP error mapping. API modules do not build Docker commands.

### `core/`

Defines transport-independent event and remediation record models. `EventType` and `EventState` are the shared vocabulary used by the parser, router, and playbooks.

### `playbooks/`

Owns response policy and workflow orchestration. The router decides which playbook applies; the container playbook coordinates services without embedding raw SQL or arbitrary shell construction.

### `services/`

Encapsulates integrations and stateful controls: Docker execution, guard state, JSONL audit, and MariaDB access.

## Data Flows

### Detection Flow

1. Zabbix Agent 2 collects Linux and Docker metrics.
2. Zabbix Server evaluates the configured `HIGH_CPU`, `CONTAINER_DOWN`, and `CONTAINER_UNHEALTHY` triggers.
3. A Zabbix Action forwards the event and its tags to the Mini-SOAR webhook.
4. FastAPI validates the payload as `ZabbixEvent`.
5. The parser maps `event_value == 1` to `PROBLEM`; any other value maps to `RECOVERY`.

### Routing and Recovery Flow

1. The router stops `RECOVERY` events after logging them.
2. `HIGH_CPU` problems enter the investigation-only playbook.
3. Container problems enter the remediation guard.
4. Unknown event types are logged without a remediation action.

### Remediation Flow

For `CONTAINER_DOWN`:

1. Acquire the guard for the event ID and service.
2. Collect recent container logs.
3. Inspect the container running state.
4. Run `docker start demo-web` when it is stopped.
5. Poll running state and Docker health for up to 90 seconds.

For `CONTAINER_UNHEALTHY`:

1. Acquire the same guard controls.
2. Collect recent container logs.
3. Restart the container when it is running; defensively start it if it has stopped before remediation.
4. Poll running state and Docker health for up to 90 seconds.

The demo workload stores its simulated unhealthy flag in process memory. A container restart resets that state and allows its `/health` endpoint to recover.

### Guard Flow

Guard checks execute atomically under a Python thread lock:

1. Remove deduplication entries older than 600 seconds.
2. Reject an already-acquired event ID as `duplicate_event`.
3. Reject another event for an active container as `remediation_in_progress`.
4. Reject a new event during the 60-second successful-remediation cooldown as `cooldown_active`.
5. Record the event ID and mark the container in progress only after the temporary checks pass.

The playbook releases the container in a `finally` block. Cooldown begins only when verification succeeds.

### Audit Flow

1. The playbook builds a record containing event, action, status, duration, and message fields.
2. `AuditService` appends the JSON record to `logs/remediation.jsonl` under a process-local thread lock.
3. It attempts a parameterized MariaDB insert into `remediation_history`.
4. MariaDB exceptions are logged and suppressed so a completed remediation does not become an application exception solely because database persistence failed.
5. The remediation API queries MariaDB for recent records or the latest record for an event ID.

## Safety Boundaries

- `DockerService` permits only `demo-web` by default.
- Docker commands are fixed argument lists passed to `subprocess.run`; webhook data is not evaluated by a shell.
- Each Docker command has a 15-second timeout.
- Container actions are followed by explicit state and health polling.
- Duplicate, lock, and cooldown denials are audited as `SKIPPED`.
- SQL values are passed as PyMySQL parameters.
- Runtime credentials come from environment variables and are excluded from Git.
- `RECOVERY` events never re-enter the remediation path.

## Runtime and Failure Behavior

- Webhook processing is synchronous. A container event can keep the HTTP request open while verification runs for up to 90 seconds.
- Guard state is in memory and is not shared across multiple worker processes or retained after restart.
- JSONL writes occur before database inserts. A database outage is non-fatal to the remediation flow, but a local audit-file write error is not currently isolated.
- MariaDB is required for the remediation history endpoints; database failures are exposed as HTTP `503`.
- The webhook and remediation history endpoints do not currently implement authentication or authorization.
- The Python webhook handler does not enforce the `managed_by` tag; Zabbix Action filtering, network restriction, and the Docker allowlist are the current boundaries.
- There is no durable queue, retry scheduler, distributed lock, or circuit breaker.

These are documented constraints and candidates for later hardening, not capabilities claimed by the current implementation.

## Phase Status

| Phase | Scope | Status |
|---|---|---|
| 1 | Infrastructure and Docker workload | Complete |
| 2 | Zabbix monitoring and detection | Complete |
| 3 | Webhook ingestion, parsing, and routing | Complete |
| 4 | Guarded remediation, verification, audit, persistence, and history API | Complete |
| 5+ | Dashboard, notifications, CI/CD, and production hardening | Planned |
