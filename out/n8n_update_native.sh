#!/usr/bin/env bash
set -euo pipefail
# Update script for native n8n deployment
docker pull n8nio/n8n:latest
docker pull postgres:16
docker rm -f n8n || true
docker rm -f n8n-postgres || true
echo "Re-run original setup script to recreate containers (data preserved in volumes)"
