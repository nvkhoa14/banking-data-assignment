#!/usr/bin/env bash
set -euo pipefail

echo ">> Running 01-init.sh: creating extensions and initial grants"

# Use psql’s ON_ERROR_STOP so the script exits on any SQL error
psql -v ON_ERROR_STOP=1 \
     --username "$POSTGRES_USER" \
     --dbname   "$POSTGRES_DB"

echo ">> 01-init.sh completed successfully"
