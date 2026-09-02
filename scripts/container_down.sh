#!/bin/bash

CONTAINER="demo-web"

echo "[*] Stopping $CONTAINER"

docker stop "$CONTAINER"

echo "[+] Container stopped"
echo "[*] Zabbix should detect CONTAINER_DOWN"
