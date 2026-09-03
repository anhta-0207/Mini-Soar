# Zabbix Monitoring and Event Forwarding

## Role in Mini-SOAR

Zabbix provides the monitoring and detection layer. Zabbix Agent 2 collects Linux and Docker telemetry from `192.168.136.110`; Zabbix Server at `192.168.136.102` evaluates triggers and forwards events to the Mini-SOAR API.

```text
demo-web and Linux host
        |
        v
Zabbix Agent 2
        |
        v
Zabbix Server
        |
        v
Trigger -> Action -> Webhook
        |
        v
http://192.168.136.110:9000/api/v1/webhooks/zabbix
```

## Monitored Data

The lab monitors Linux host telemetry and Docker workload state. Docker data used by the project includes:

- container CPU and memory usage;
- running state;
- Docker health state;
- restart count;
- OOMKilled state;
- discovered container metadata.

The custom Docker discovery must retain stopped containers. `CONTAINER_DOWN` depends on the running-state item remaining available after `demo-web` stops.

## Docker Socket Access

Zabbix Agent 2 needs access to the Docker daemon for the configured Docker items. In this isolated lab the agent account may be granted Docker group access.

Docker socket access is effectively privileged host access. This lab configuration should not be copied into production without a least-privilege review and a safer collection boundary.

## Detection Events

| Event type | Meaning | Mini-SOAR policy |
|---|---|---|
| `HIGH_CPU` | Sustained high CPU for `demo-web` | Investigation-only; no automatic restart |
| `CONTAINER_DOWN` | The container running state is false | Start and verify `demo-web` |
| `CONTAINER_UNHEALTHY` | Docker health reports unhealthy | Restart and verify `demo-web` |

Exact documented expressions and expected recovery behavior are in [triggers.md](triggers.md).

## Required Event Tags

The event parser routes behavior from trigger tags, not from free-form event names. Each managed trigger should provide:

| Tag | Example | Purpose |
|---|---|---|
| `event_type` | `CONTAINER_DOWN` | Maps to the internal `EventType` enum |
| `service` | `demo-web` | Identifies the allowlisted remediation target |
| `managed_by` | `mini-soar` | Identifies ownership in Zabbix configuration and filtering |

The current Python parser consumes `event_type` and `service`. `managed_by` remains useful on the Zabbix side for action conditions and operator visibility.

## Webhook Contract

Mini-SOAR accepts:

```text
POST /api/v1/webhooks/zabbix
Content-Type: application/json
```

The request model requires:

- `event_id`;
- `event_name`;
- `event_value`;
- `severity`;
- `host`;
- `trigger_id`;
- `tags`, represented as `tag`/`value` objects.

`source` is optional and defaults to `zabbix`.

Example normalized payload shape:

```json
{
  "source": "zabbix",
  "event_id": "1211",
  "event_name": "[Mini-SOAR] demo-web Container unhealthy",
  "event_value": 1,
  "severity": "High",
  "host": "lab-server_192.168.136.110",
  "trigger_id": "12345",
  "tags": [
    {"tag": "event_type", "value": "CONTAINER_UNHEALTHY"},
    {"tag": "service", "value": "demo-web"},
    {"tag": "managed_by", "value": "mini-soar"}
  ]
}
```

The media type/action in the live Zabbix instance is responsible for translating Zabbix macros into this JSON shape. The webhook script or media type export is not stored in this repository, so this documentation does not reconstruct or claim an importable Zabbix configuration.

## State Handling

The parser maps `event_value == 1` to `PROBLEM`. Other values map to `RECOVERY`.

- `PROBLEM` events are routed by event type.
- `RECOVERY` events are logged and return without remediation.
- Unsupported or missing `event_type` values become `UNKNOWN` and produce a warning without a Docker action.

## Action and Delivery Notes

- The action should target only events tagged for Mini-SOAR management.
- The Python handler does not currently reject events with a missing or different `managed_by` tag; enforce this selection in the Zabbix Action and restrict network access to the webhook.
- The webhook destination is Mini-SOAR port `9000`, not the `demo-web` application on port `8000`.
- The current FastAPI handler performs routing synchronously before returning the accepted response.
- Repeated delivery of an acquired event ID is handled by the in-memory remediation guard and audited as `SKIPPED`.
- The current endpoint has no authentication; network restriction is required in this lab and API authentication remains a hardening item.

## Evidence

- [Zabbix action forwarding](../docs/images/09-zabbix-action-forwarder.png)
- [Webhook media type configuration](../docs/images/10-zabbix-webhook.png)
- [End-to-end event delivery](../docs/images/15-end-to-end-event-pipeline.png)
- [Zabbix action log](../docs/images/16-zabbix-action-log.png)

## Template Export

The custom Docker template is configured in the live Zabbix environment but has not been committed as an export. See [templates/README.md](templates/README.md) for the policy and manual export workflow. Do not generate a replacement YAML file from documentation alone.
