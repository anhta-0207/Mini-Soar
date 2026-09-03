from fastapi import FastAPI, HTTPException

app = FastAPI(
    title="Mini-SOAR Demo Workload",
    version="1.0.0",
)

# Lab-only simulated fault.
# This value resets to False whenever the application process restarts.
force_unhealthy = False


@app.get("/")
def root():
    return {
        "service": "demo-web",
        "status": "running",
    }


@app.get("/health")
def health():
    if force_unhealthy:
        raise HTTPException(
            status_code=503,
            detail="Simulated unhealthy state",
        )

    return {
        "status": "healthy",
    }


@app.post("/simulate/unhealthy")
def simulate_unhealthy():
    global force_unhealthy

    force_unhealthy = True

    return {
        "status": "ok",
        "message": "Unhealthy state enabled",
    }


@app.post("/simulate/recover")
def simulate_recover():
    global force_unhealthy

    force_unhealthy = False

    return {
        "status": "ok",
        "message": "Unhealthy state disabled",
    }


@app.get("/simulate/status")
def simulation_status():
    return {
        "force_unhealthy": force_unhealthy,
    }
