# Mini-SOAR Architecture

## Current Architecture

The current repository implements monitoring and detection. Its responsibility ends when Zabbix creates a `PROBLEM` or recovery event.

```text
Linux Server
     |
     +-----------------------+
     |                       |
     v                       v
Linux telemetry        Docker daemon
                             |
                             v
                         demo-web
     |                       |
     +-----------+-----------+
                 |
                 v
          Zabbix Agent 2
                 |
                 v
           Zabbix Server
                 |
                 v
          Detection Rules
        /        |          \
       v         v           v
 HIGH_CPU  CONTAINER_DOWN  CONTAINER_UNHEALTHY
        \        |          /
         +-------+---------+
                 |
                 v
           PROBLEM Event
```

### Component responsibilities

| Component | Current responsibility |
|---|---|
| Linux server | Hosts the monitored system, Docker runtime, and Zabbix Agent 2 |
| `demo-web` | Provides the controlled FastAPI workload and Docker health endpoint |
| Zabbix Agent 2 | Collects Linux and Docker telemetry from the monitored host |
| Zabbix Server | Stores monitoring data, evaluates triggers, and creates events |
| Detection rules | Identify sustained high CPU, container down, and unhealthy states |

### Phase 2 scope

- Linux telemetry collection
- Docker telemetry collection
- Docker container discovery
- Container CPU and memory monitoring
- Running, health, restart count, and OOMKilled monitoring
- `HIGH_CPU`, `CONTAINER_DOWN`, and `CONTAINER_UNHEALTHY` detection
- Zabbix `PROBLEM` and recovery events

## Planned Architecture

The following components belong to later phases. They are architectural targets, not currently deployed features:

```text
Zabbix PROBLEM Event
         |
         v
      Webhook
         |
         v
  Mini-SOAR Engine
         |
         v
   Playbook Engine
         |
         v
Automated Remediation
         |
         v
     Verification
         |
         v
   Telegram Report
```

Planned supporting capabilities include MariaDB incident storage and Jenkins CI/CD. Their implementation and security boundaries will be documented when those phases begin.
