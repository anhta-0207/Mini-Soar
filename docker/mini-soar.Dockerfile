FROM python:3.12-slim-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Mini-SOAR DockerService uses the Docker CLI through subprocess.
# Only the host Docker daemon is used; no Docker daemon runs here.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        docker.io \
        ca-certificates \
    && docker --version \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install \
    --no-cache-dir \
    -r requirements.txt

COPY src ./src

EXPOSE 9000

HEALTHCHECK \
    --interval=15s \
    --timeout=5s \
    --start-period=10s \
    --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:9000/health')" || exit 1

CMD ["uvicorn", "mini_soar.main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "9000"]
