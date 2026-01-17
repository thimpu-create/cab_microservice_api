#!/bin/sh
set -e

echo "Waiting for PostgreSQL to be ready..."
until pg_isready -h postgres -p 5432 -U postgres; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "PostgreSQL is up - checking database..."
# Create database if it doesn't exist (using postgres database to connect)
PGPASSWORD=password psql -h postgres -U postgres -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'driverdb'" | grep -q 1 || \
PGPASSWORD=password psql -h postgres -U postgres -d postgres -c "CREATE DATABASE driverdb"

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000
