# Zabbix Detection Rules

Mini-SOAR currently uses three custom Zabbix triggers as its detection layer. The expressions below are preserved from the existing lab configuration and are the repository's source of truth.

## HIGH_CPU

| Field | Value |
|---|---|
| Trigger name | `[Mini-SOAR] demo-web High CPU utilization` |
| Event type | `HIGH_CPU` |
| Target | `demo-web` |
| Severity | High |
| Detection condition | Average container CPU utilization over two minutes exceeds 80% |
| Purpose | Detect sustained CPU pressure on the monitored workload |

### Current expression

```text
avg(/lab-server_192.168.136.110/docker.container_stats.cpu_pct_usage["/demo-web"],2m)>80
```

### Expected recovery behavior

The event should recover after the two-minute average no longer exceeds 80%. Because the rule uses a moving average, recovery may occur after the simulated load has already stopped.

## CONTAINER_DOWN

| Field | Value |
|---|---|
| Trigger name | `[Mini-SOAR] demo-web Container down` |
| Event type | `CONTAINER_DOWN` |
| Target | `demo-web` |
| Severity | High |
| Detection condition | The container running-state item becomes false (`0`) |
| Purpose | Detect loss of the monitored container process |

### Current expression

```text
last(/lab-server_192.168.136.110/docker.container_info.state.running["/demo-web"])=0
```

### Expected recovery behavior

The event should recover after `demo-web` is started again and Zabbix receives a running-state value of true (`1`). Stopped containers must remain discoverable so the state item remains available during the incident.

## CONTAINER_UNHEALTHY

| Field | Value |
|---|---|
| Trigger name | `[Mini-SOAR] demo-web Container unhealthy` |
| Event type | `CONTAINER_UNHEALTHY` |
| Target | `demo-web` |
| Severity | High |
| Detection condition | Docker reports health state `2` (unhealthy) for `demo-web` |
| Purpose | Detect application health failure while the workload is monitored as a container |

### Current expression

```text
last(/lab-server_192.168.136.110/docker.container_info.state.health["/demo-web"])=2
```

The operational scenario assumes the container is still running while Docker reports it as unhealthy. The current stored expression evaluates the health item directly; it does not add a separate running-state predicate.

### Expected recovery behavior

The event should recover after the cause of the failed health check is removed and Docker reports a health value other than unhealthy. Zabbix recovery follows the next collected healthy state and the trigger evaluation interval.
