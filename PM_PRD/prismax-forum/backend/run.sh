#!/usr/bin/env bash
# Launch the Prisma(x) Forum API.
set -e
cd "$(dirname "$0")"
exec .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8085}" "$@"
