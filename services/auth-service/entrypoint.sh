#!/bin/sh

echo "Running Alembic migrations..."
alembic upgrade head

echo "Seeding roles (only if empty)..."
python seed_roles.py

echo "Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000
