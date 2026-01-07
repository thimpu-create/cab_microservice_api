#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."
until pg_isready -h postgres -p 5432; do
  sleep 2
done

echo "Ensuring database exists..."
psql -h postgres -U postgres -tc "SELECT 1 FROM pg_database WHERE datname='companydb'" | grep -q 1 \
  || psql -h postgres -U postgres -c "CREATE DATABASE companydb;"

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000
