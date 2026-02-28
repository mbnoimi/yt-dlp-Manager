#!/bin/bash
set -e

mkdir -p /app/data/global /app/backend/logs
chown -R appuser:appuser /app/data /app/backend/logs 2>/dev/null || true

exec gosu appuser "$@"
