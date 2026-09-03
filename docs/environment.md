# Mini-SOAR Lab Environment

## Scope

Mini-SOAR runs in an isolated Linux lab. The monitored Docker workload, Zabbix Agent 2, and Mini-SOAR engine are hosted on the same server; Zabbix Server runs on a separate lab node.

No password, token, private key, or other credential belongs in this document.

## Topology

| Component | Address or location | Purpose |
|---|---|---|
| Monitored host | `192.168.136.110` | Runs Docker, `demo-web`, Zabbix Agent 2, and Mini-SOAR |
| Zabbix Server | `192.168.136.102` | Collects telemetry, evaluates triggers, and sends webhook events |
| `demo-web` | `192.168.136.110:8000` | Controlled FastAPI workload and Docker health target |
| Mini-SOAR API | `192.168.136.110:9000` | Webhook ingestion, process health, and remediation history API |
| MariaDB | Local to the monitored host | Stores the `mini_soar.remediation_history` audit table |

These private addresses describe the current lab and should be adjusted for another environment.

## Runtime Components

### Demo Workload

The root `Dockerfile` builds the monitored FastAPI workload from `app/main.py`. It exposes port `8000` and defines a Docker health check against `GET /health`.

Available workload endpoints are:

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | Basic workload identity |
| `GET` | `/health` | Docker application health check |
| `POST` | `/simulate/unhealthy` | Enable the lab-only in-memory failure state |
| `POST` | `/simulate/recover` | Clear the in-memory failure state |
| `GET` | `/simulate/status` | Inspect the current simulation flag |

The simulation flag resets when the application process or container restarts.

Example build and run commands for a fresh lab container:

```bash
docker build -t mini-soar-demo-web .
docker run -d \
  --name demo-web \
  --restart unless-stopped \
  -p 8000:8000 \
  mini-soar-demo-web
```

### Mini-SOAR Engine

Create an isolated Python environment and install the tracked dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Start the API on port `9000`:

```bash
python -m uvicorn mini_soar.main:app \
  --app-dir src \
  --host 0.0.0.0 \
  --port 9000
```

The account running Mini-SOAR must be able to invoke the Docker CLI against the local daemon. Docker daemon access is highly privileged; grant it only inside the intended lab boundary.

## Environment Variables

Copy the placeholder file and set local values without committing them:

```bash
cp .env.example .env
```

`DatabaseService` currently reads these variables:

| Variable | Default in code | Purpose |
|---|---|---|
| `DB_HOST` | `127.0.0.1` | MariaDB host |
| `DB_PORT` | `3306` | MariaDB port |
| `DB_NAME` | `mini_soar` | Database name |
| `DB_USER` | `mini_soar` | Database account |
| `DB_PASSWORD` | Empty | Database password; set this locally |

The API ports are supplied to Uvicorn in the current implementation; they are not read from application environment variables.

## MariaDB

The application expects a database named `mini_soar` and the table defined by `database/schema.sql`. Provision the database and account according to the local MariaDB policy, then apply the tracked schema with an authorized account:

```bash
mariadb -u mini_soar -p mini_soar < database/schema.sql
```

Do not place the password in the command line, repository, shell history, or documentation.

## Connectivity

The required lab paths are:

| Source | Destination | Purpose |
|---|---|---|
| Zabbix Server | Monitored host TCP `9000` | Deliver Mini-SOAR webhook requests |
| Browser/operator | Monitored host TCP `8000` | Access and simulate the demo workload |
| Browser/operator | Monitored host TCP `9000` | Access Mini-SOAR health, Swagger, and remediation APIs |
| Zabbix Server | Zabbix Agent 2 TCP `10050` | Passive agent checks when used by the lab configuration |
| Mini-SOAR | Local Docker daemon | Inspect, start, restart, and verify `demo-web` |
| Mini-SOAR | Local MariaDB TCP `3306` | Persist and query remediation history |

Firewall rules should expose only the paths required by the lab.

## Verification Commands

Check the workload and Docker health:

```bash
docker ps --filter name=demo-web
docker inspect demo-web
curl -i http://localhost:8000/health
```

Check the Mini-SOAR process and API documentation:

```bash
curl -i http://localhost:9000/health
curl -s "http://localhost:9000/api/v1/remediations?limit=5"
```

Open `http://192.168.136.110:9000/docs` from a browser that can reach the lab network.

## Runtime Data

- Local remediation audit: `logs/remediation.jsonl`
- MariaDB schema: `database/schema.sql`
- Local environment values: `.env`

The `.env`, `.venv/`, `__pycache__/`, `*.pyc`, and `logs/` paths are ignored by Git.

## Current Limitations

- The webhook and history APIs have no authentication.
- Remediation executes synchronously in the API process.
- Guard state is per-process and disappears on restart.
- The current allowlist supports only `demo-web`.
- MariaDB must be reachable for history API queries.
- Dashboard, notification, Jenkins, and durable worker components are not deployed.
