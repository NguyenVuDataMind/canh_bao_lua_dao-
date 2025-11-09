#!/bin/bash
set -e

echo "=== Entrypoint Script ==="

# Fix permissions for Hugging Face cache directory
# This needs to run as root to chown the volume
echo "Fixing permissions for /app/.cache/huggingface..."
mkdir -p /app/.cache/huggingface
chown -R app:app /app/.cache/huggingface || true
chmod -R 755 /app/.cache/huggingface || true

# Switch to app user and run migrations + server
echo "Switching to app user and starting application..."
exec gosu app sh -c "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 5000"

