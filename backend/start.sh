#!/bin/bash

# Apply Database Schema (if needed)
# Note: Ideally this is done via migration tool (alembic), but for now we apply the DDL for the new schema
echo "Applying Master Schema..."
# Wait for DB to be ready
sleep 5
PGPASSWORD=$DB_PASSWORD psql -h db -U $DB_USER -d $DB_NAME -f src/infrastructure/database/master_schema.sql || echo "Schema application warning (ignore if exists)"

# Start Scheduler in Background
echo "Starting Scheduler..."
python src/scripts/scheduler.py &

# Start Main API
echo "Starting API..."
uvicorn src.interfaces.api.main:app --host 0.0.0.0 --port 8000
