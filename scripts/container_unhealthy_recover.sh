#!/bin/bash

set -e

URL="http://localhost:8000"

echo "[*] Clearing simulated unhealthy state..."

curl -fsS \
  -X POST \
  "$URL/simulate/recover"

echo
echo "[+] Fault cleared"
