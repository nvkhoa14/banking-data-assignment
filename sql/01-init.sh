#!/usr/bin/env bash
set -e

# Apply schema.sql into the target DB (POSTGRES_DB defaults to 'postgres' if unset)
echo "=> Applying schema"
psql \
  --username "$POSTGRES_USER" \
  --dbname   "$POSTGRES_DB" \
  -f /docker-entrypoint-initdb.d/schema.sql

# Run data generation
echo "=> Generating sample data"
python3 /docker-entrypoint-initdb.d/generate_data.py
echo "=> Initialization complete"

# Run data quality checks
echo "=> Running data quality checks"
python3 /docker-entrypoint-initdb.d/data_quality_standards.py
echo "=> Data quality checks completed"


# Run monitoring and auditing script
echo "=> Starting monitoring and auditing"
python3 /docker-entrypoint-initdb.d/monitoring_audit.py
echo "=> Monitoring and auditing started"