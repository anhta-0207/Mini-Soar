# Zabbix Monitoring

## Role in Mini-SOAR

Zabbix is the monitoring and detection layer of Mini-SOAR. In the current implementation, it collects Linux and Docker telemetry, evaluates detection rules, and creates `PROBLEM` and recovery events. The future Mini-SOAR engine will consume those events through a webhook; that integration is not implemented yet.

## Zabbix Agent 2

Zabbix Agent 2 runs on the monitored Linux server. It provides host telemetry and the Docker integration used to monitor local containers. The lab uses:

- the **Linux by Zabbix agent** template for host-level monitoring;
- a custom Docker template for Mini-SOAR container discovery and telemetry;
- Zabbix triggers for incident detection.

The exported custom Docker template is not stored in this repository yet. It will be exported manually from Zabbix and added under [`templates/`](templates/).

## Docker Monitoring

Zabbix Agent 2 reads Docker information from the Docker daemon and exposes container telemetry to Zabbix Server. The lab monitors the `demo-web` workload, including:

- container CPU usage;
- container memory usage;
- running state;
- Docker health status;
- restart count;
- OOMKilled state.

### Docker socket access

The agent account needs permission to communicate with the Docker socket in this lab. Depending on the host configuration, the `zabbix` account may be added to the Docker group.

Docker group membership effectively grants highly privileged access to the host. This is acceptable for this isolated lab, but it must be treated carefully in production. Production designs should minimize socket access, apply least privilege, and assess safer collection boundaries.

## Docker Low-Level Discovery

Docker Low-Level Discovery (LLD) creates monitoring items for discovered containers. The custom Mini-SOAR Docker template must continue discovering stopped containers, not only running containers.

This behavior matters because `CONTAINER_DOWN` depends on the running-state item remaining available after `demo-web` stops. If stopped containers disappear from discovery immediately, Zabbix may lose the telemetry needed to evaluate the down condition reliably.

## Detection Triggers

The current custom events are:

| Event | Target | Detection purpose |
|---|---|---|
| `HIGH_CPU` | `demo-web` | Detect sustained high container CPU utilization |
| `CONTAINER_DOWN` | `demo-web` | Detect when the container is no longer running |
| `CONTAINER_UNHEALTHY` | `demo-web` | Detect an unhealthy Docker health state |

The source-of-truth expressions, severity, purpose, and expected recovery behavior are documented in [triggers.md](triggers.md).

## Future Mini-SOAR Integration

The planned event path is:

```text
Zabbix PROBLEM event
        |
        v
Webhook
        |
        v
Mini-SOAR engine
```

In a later phase, the engine is expected to classify events, select remediation playbooks, verify recovery, and report outcomes. Zabbix currently stops at monitoring, trigger evaluation, and event generation; the webhook and automated response pipeline are not part of the current implementation.
