# Zabbix Detection Rules

Mini-SOAR uses three documented Zabbix triggers for the `demo-web` workload. The expressions below reflect the lab configuration recorded in this repository. Because no exported Zabbix template is committed, verify them against the live Zabbix instance after configuration changes.

## Common Tags

Each managed trigger should include:

| Tag | Value |
|---|---|
| `managed_by` | `mini-soar` |
| `service` | `demo-web` |
| `event_type` | Event-specific value shown below |

These tags drive Zabbix Action selection and Mini-SOAR routing. They must use the exact enum values expected by the application.

## `HIGH_CPU`

| Field | Value |
|---|---|
| Trigger name | `[Mini-SOAR] demo-web High CPU utilization` |
| `event_type` tag | `HIGH_CPU` |
| Severity | High |
| Detection condition | Average container CPU utilization over two minutes exceeds 80% |
| Mini-SOAR response | Investigation-only dry run |

### Documented Expression

```text
avg(/lab-server_192.168.136.110/docker.container_stats.cpu_pct_usage["/demo-web"],2m)>80
```

### Recovery

The problem recovers after the two-minute average no longer exceeds 80%. Recovery may lag behind stopping the injected workload because the expression uses a moving window.

Mini-SOAR intentionally does not restart `demo-web` for this event. High CPU can have valid causes and does not by itself establish that a restart is the safest response.

## `CONTAINER_DOWN`

| Field | Value |
|---|---|
| Trigger name | `[Mini-SOAR] demo-web Container down` |
| `event_type` tag | `CONTAINER_DOWN` |
| Severity | High |
| Detection condition | Container running state becomes false (`0`) |
| Mini-SOAR response | Start the allowlisted container and verify it |

### Documented Expression

```text
last(/lab-server_192.168.136.110/docker.container_info.state.running["/demo-web"])=0
```

### Recovery

The event recovers after Mini-SOAR starts `demo-web` and Zabbix receives a running-state value of `1`. Docker discovery must keep stopped containers visible so this item remains available during the incident.

## `CONTAINER_UNHEALTHY`

| Field | Value |
|---|---|
| Trigger name | `[Mini-SOAR] demo-web Container unhealthy` |
| `event_type` tag | `CONTAINER_UNHEALTHY` |
| Severity | High |
| Detection condition | Docker reports health state `2` (`unhealthy`) |
| Mini-SOAR response | Restart the running container and verify it |

### Documented Expression

```text
last(/lab-server_192.168.136.110/docker.container_info.state.health["/demo-web"])=2
```

The stored expression evaluates Docker health directly and does not contain a separate running-state predicate. The operational scenario assumes the container is still running while unhealthy. The playbook defensively starts it if it has stopped before remediation begins.

### Recovery

The demo workload's lab-only fault state is held in process memory. Restarting `demo-web` clears the state, its health endpoint returns success, Docker reports `healthy`, and Zabbix emits a recovery event.

## Event Lifecycle

```text
Metric change
    -> Zabbix PROBLEM
    -> Action and webhook
    -> Mini-SOAR route
    -> Optional guarded remediation
    -> Zabbix RECOVERY
    -> Mini-SOAR logs recovery only
```

Zabbix may retry or deliver repeated event notifications. Mini-SOAR deduplicates an acquired event ID in memory and writes duplicate decisions as `SKIPPED` audit records.

## Validation

Use the controlled scripts documented in [scripts/README.md](../scripts/README.md). During self-healing tests, do not manually recover the container before Mini-SOAR has a chance to act.

The current screenshots include:

- [HIGH_CPU problem](../docs/images/06-high-cpu-problem.png)
- [Container down and unhealthy problems](../docs/images/07-container-down&unhealthy-problem.png)
- [Resolved problems](../docs/images/08-problem-resolved.png)
- [Container routing evidence](../docs/images/11-container-down-routing.png)
- [Unhealthy routing evidence](../docs/images/13-container-unhealthy-routing.png)
- [HIGH_CPU investigation policy](../docs/images/14-high-cpu-routing.png)
