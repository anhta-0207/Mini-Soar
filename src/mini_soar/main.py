import logging

from fastapi import FastAPI

from mini_soar.api.zabbix import router as zabbix_router


logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s "
        "%(levelname)s "
        "%(name)s "
        "%(message)s"
    ),
)


app = FastAPI(
    title="Mini-SOAR Engine",
    version="0.1.0",
)


app.include_router(
    zabbix_router,
    prefix="/api/v1",
)


@app.get("/health")
def health():
    return {
        "service": "mini-soar-engine",
        "status": "healthy",
    }
