#!/bin/bash
set -e

echo "=== Entrypoint Script ==="

# Fix permissions for Hugging Face cache directory
# This needs to run as root to chown the volume
echo "Fixing permissions for /app/.cache/huggingface..."
mkdir -p /app/.cache/huggingface
chown -R app:app /app/.cache/huggingface || true
chmod -R 755 /app/.cache/huggingface || true

# Run migrations and server as root (temporary solution for permission issues)
# TODO: Fix permissions properly to run as app user
echo "Running migrations and starting application..."
alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 5000

