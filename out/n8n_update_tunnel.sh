#!/usr/bin/env bash
set -euo pipefail
# Update script for tunnel (compose) n8n deployment
cd "$HOME/n8n-stack"
docker compose pull
docker compose up -d --force-recreate n8n
echo "Updated n8n container (DB persisted)."
