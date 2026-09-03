from fastapi import FastAPI, HTTPException
from pathlib import Path
app = FastAPI(
    title="Mini-SOAR Demo Application",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "service": "demo-web",
        "status": "running"
    }



@app.get("/health")
def health():
    if Path("/tmp/force_unhealthy").exists():
        raise HTTPException(
            status_code=503,
            detail="Simulated unhealthy state"
        )

    return {"status": "healthy"}
