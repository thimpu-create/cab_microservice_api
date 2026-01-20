# Database Setup for Realtime Service

## Initial Setup

The realtime-service requires a PostgreSQL database named `realtimedb`.

### Create Database

If the database doesn't exist, create it using one of these methods:

#### Method 1: Using Docker (Recommended)
```bash
docker exec postgres psql -U postgres -c "CREATE DATABASE realtimedb;"
```

#### Method 2: Using psql directly
```bash
psql -h localhost -U postgres -c "CREATE DATABASE realtimedb;"
```

#### Method 3: Using Python script (from inside container)
```bash
# First, ensure you're in the container with psycopg2 installed
python create_database.py
```

## Running Migrations

After the database is created, run migrations:

```bash
# From inside the realtime-service container or directory
alembic revision --autogenerate -m "create_rides_table"
alembic upgrade head
```

## Database Configuration

The database connection is configured in:
- `app/db/session.py` - Database session setup
- `app/core/config.py` - Settings (can use environment variables)
- `alembic.ini` - Alembic configuration

### Environment Variables

You can override the database URL using:
```env
DATABASE_URL=postgresql://postgres:password@postgres:5432/realtimedb
```

Or set individual components:
```env
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
```

## Troubleshooting

### Error: "database realtimedb does not exist"
- Run the database creation command above
- Verify the database exists: `docker exec postgres psql -U postgres -l`

### Error: "connection refused"
- Ensure postgres container is running: `docker ps | grep postgres`
- Check network connectivity: `docker network ls`

### Error: "authentication failed"
- Verify POSTGRES_USER and POSTGRES_PASSWORD in .env file
- Check postgres container logs: `docker logs postgres`
