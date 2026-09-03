#!/bin/bash

CONTAINER="demo-web"

echo "[*] Starting CPU spike inside $CONTAINER"

docker exec -d "$CONTAINER" \
    python -c "while True: pass"

echo "[+] CPU spike started"
echo "[*] Check with: docker stats $CONTAINER"
