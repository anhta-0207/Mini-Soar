#!/bin/bash

set -e

URL="http://localhost:8000"

echo "[*] Simulating unhealthy state for demo-web..."

curl -fsS \
  -X POST \
  "$URL/simulate/unhealthy"

echo
echo "[+] Fault injected successfully"
echo "[*] Waiting for Docker healthcheck to detect the failure..."
