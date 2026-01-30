#!/bin/bash

# Apply Database Schema (if needed)
# Note: Ideally this is done via migration tool (alembic), but for now we apply the DDL for the new schema
echo "Applying Master Schema..."
# Wait for DB to be ready
sleep 5
# Apply Database Migrations / Seed
echo "Checking Database..."
# Debug: Print DB URL (Masked)
echo "Environment DATABASE_URL: $(echo $DATABASE_URL | sed 's/:[^:@]*@/:***@/')"
python seed.py
if [ $? -ne 0 ]; then
    echo "ERROR: Database seed failed. Exiting."
    exit 1
fi

# Start Scheduler in Background
echo "Starting Scheduler..."
python src/scripts/scheduler.py &

# Start Main API
echo "Starting API..."
uvicorn src.interfaces.api.main:app --host 0.0.0.0 --port 8000
