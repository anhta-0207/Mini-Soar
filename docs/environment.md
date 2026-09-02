# Lab Environment

## Overview

Mini-SOAR is developed in an isolated Linux lab for infrastructure monitoring, anomaly detection, and future self-healing automation. The currently deployed scope covers the monitored host, Docker workload, Zabbix data collection, and detection events.

## Current Infrastructure

| Component | Value |
|---|---|
| Host | `lab-server` |
| Operating system | Linux |
| Container runtime | Docker |
| Monitoring agent | Zabbix Agent 2 |
| Monitoring platform | Zabbix Server |
| Demo application | Python FastAPI |
| Demo container | `demo-web` |
| Application port | `8000` |
| Zabbix Agent port | `10050` |

Environment-specific addresses and credentials are intentionally omitted.

## Demo Workload

The `demo-web` container is a controlled workload for testing monitoring and detection. It provides:

- a FastAPI service on port `8000`;
- a `GET /health` endpoint;
- a Docker `HEALTHCHECK`;
- controlled CPU, stopped-container, and unhealthy-container test scenarios.

## Monitoring Path

```text
Linux host and Docker daemon
            |
            v
      Zabbix Agent 2
            |
            v
       Zabbix Server
            |
            v
    Detection triggers
            |
            v
       PROBLEM events
```

## Monitored Telemetry

Current host telemetry includes:

- CPU usage;
- memory usage;
- disk usage;
- network activity.

Current Docker telemetry includes:

- container CPU and memory usage;
- running state;
- Docker health status;
- restart count;
- OOMKilled state;
- discovered container metadata.

## Current and Planned Scope

Zabbix monitoring and detection are part of the current lab. The Python Mini-SOAR engine, webhook processing, automated remediation, MariaDB incident storage, Telegram reporting, and Jenkins CI/CD are planned for later phases and are not documented as deployed components.

## Security Notes

- No real passwords, API tokens, Telegram bot tokens, SSH keys, session cookies, or private credentials should be committed.
- `.env.example` contains placeholders only; real local values belong in the ignored `.env` file.
- Docker socket access is highly privileged and is acceptable here only within the isolated lab. See [Zabbix monitoring](../zabbix/README.md#docker-socket-access) for details.
