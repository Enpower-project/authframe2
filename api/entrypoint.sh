#!/bin/sh
set -e

echo "Updating CA trust..."
update-ca-certificates

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug --access-log