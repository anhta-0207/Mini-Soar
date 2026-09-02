from fastapi import FastAPI

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
    return {
        "status": "healthy"
    }
