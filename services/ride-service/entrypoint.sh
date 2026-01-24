#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."
until pg_isready -h postgres -p 5432 -U postgres; do
  echo "PostgreSQL unavailable - sleeping"
  sleep 1
done

echo "Creating ridedb if needed..."
PGPASSWORD=password psql -h postgres -U postgres -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'ridedb'" | grep -q 1 || \
PGPASSWORD=password psql -h postgres -U postgres -d postgres -c "CREATE DATABASE ridedb"

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting Ride Service..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
