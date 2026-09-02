#!/bin/bash

CONTAINER="demo-web"

echo "[*] Simulating unhealthy application state"

docker exec "$CONTAINER" touch /tmp/force_unhealthy

echo "[+] Failure flag created"
echo "[*] Waiting for Docker HEALTHCHECK to detect failure"
