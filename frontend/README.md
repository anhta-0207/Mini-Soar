# Mini-SOAR Dashboard

This directory contains the Phase 5 read-only security operations dashboard built with React, TypeScript, and Vite. It presents persisted remediation history and analytics from the Mini-SOAR FastAPI backend.

The UI does not expose remediation, playbook, Docker, or shell controls.

## Development

Start the backend at `127.0.0.1:9000`, then run:

```bash
npm install
npm run dev
```

Vite serves the dashboard on `0.0.0.0:5173` and proxies `/api` and `/health` to the backend. Open `http://localhost:5173` for local development.

## Available Scripts

| Command | Purpose |
|---|---|
| `npm run dev` | Start the Vite development server |
| `npm run build` | Type-check and create a production-mode bundle in `dist/` |
| `npm run lint` | Run Oxlint |
| `npm run preview` | Preview the generated bundle locally |

The repository does not currently include production hosting or deployment configuration for `dist/`.

## Backend Data

The dashboard client calls:

- `GET /api/v1/remediations`
- `GET /api/v1/remediations/summary`
- `GET /api/v1/remediations/distribution`

See the repository [README](../README.md) and [environment documentation](../docs/environment.md) for the full architecture, backend startup, and lab constraints.
