# Controlled Failure Simulation

These scripts exist only for controlled testing in the isolated Mini-SOAR lab. They intentionally consume resources or disrupt the `demo-web` workload so that Zabbix detection and recovery behavior can be verified. They are not production tooling or attack utilities.

Run them only after confirming that `demo-web` is the intended lab container and that interrupting it will not affect other users or services.

## Prerequisites

- Docker is installed and the current account can manage containers.
- The `demo-web` container has been created.
- Zabbix Agent 2 is collecting the relevant Docker items.
- The custom Zabbix detection triggers are enabled.

## `cpu_spike.sh`

### Purpose

Validate sustained CPU monitoring and the `HIGH_CPU` trigger.

### Expected state before execution

- `demo-web` is running and healthy.
- Its CPU utilization is below the trigger threshold.

### Simulated failure

The script starts a detached Python busy loop inside `demo-web`, creating sustained container CPU load.

### Expected Zabbix event

`HIGH_CPU` — `[Mini-SOAR] demo-web High CPU utilization`

The trigger uses a two-minute average, so detection and recovery are not immediate.

### Restore the environment

Restart the lab container to stop the detached busy loop:

```bash
docker restart demo-web
```

Confirm that the service becomes healthy again and wait for the average CPU value to fall below the configured threshold.

## `container_down.sh`

### Purpose

Validate running-state monitoring and the `CONTAINER_DOWN` trigger.

### Expected state before execution

- `demo-web` exists and is running.
- Zabbix is collecting its running-state item.

### Simulated failure

The script stops `demo-web` with `docker stop`.

### Expected Zabbix event

`CONTAINER_DOWN` — `[Mini-SOAR] demo-web Container down`

### Restore the environment

Start the stopped container:

```bash
docker start demo-web
```

Confirm that the container is running and wait for Zabbix to collect the recovered running state.

## `container_unhealthy.sh`

### Purpose

Validate Docker health-state monitoring and the `CONTAINER_UNHEALTHY` trigger.

### Expected state before execution

- `demo-web` is running and healthy.
- The deployed lab health-check implementation is configured to fail when `/tmp/force_unhealthy` exists inside the container.

### Simulated failure

The script creates `/tmp/force_unhealthy` inside the running container. In the configured lab workload, this flag is intended to make subsequent Docker health checks fail without stopping the container.

### Expected Zabbix event

`CONTAINER_UNHEALTHY` — `[Mini-SOAR] demo-web Container unhealthy`

### Restore the environment

Remove the failure flag:

```bash
docker exec demo-web rm -f /tmp/force_unhealthy
```

If the health state does not recover, restart the lab container:

```bash
docker restart demo-web
```

Wait for Docker to report `healthy` and for Zabbix to collect the recovered health state.

> Note: the FastAPI `/health` handler currently stored in this repository always returns a healthy response. Verify that the deployed lab health-check behavior interprets `/tmp/force_unhealthy` before relying on this simulation.
