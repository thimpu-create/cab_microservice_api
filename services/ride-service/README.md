# Ride Service

Ride domain service. Owns **VehicleType**, **RideRequest** schemas, and ride persistence.

## Role

- **ride-service**: Ride CRUD, persistence (Postgres), business rules. Exposes internal API for realtime-service.
- **realtime-service**: WebSockets, matching, Redis, live updates. Calls ride-service for ride operations.

## Flow

1. **Request ride**: Client → realtime `POST /rides/request` → realtime calls ride-service `POST /internal/rides/request` → gets `request_id` → matching, Redis, WebSocket broadcast.
2. **Assign**: Driver accepts → realtime updates Redis → realtime calls ride-service `PATCH .../status` (assigned, driver_id).
3. **Start/Complete**: Driver updates status → realtime updates Redis → realtime calls ride-service `PATCH .../status` (in_progress | completed).
4. **Cancel**: Client → realtime `POST /rides/{id}/cancel` → realtime calls ride-service `POST .../cancel` → realtime cleans Redis and notifies.

## Internal API (X-Internal-Key)

- `POST /api/v1/internal/rides/request` – create ride (pending)
- `GET /api/v1/internal/rides/{request_id}/status`
- `PATCH /api/v1/internal/rides/{request_id}/status` – assign | in_progress | completed
- `POST /api/v1/internal/rides/{request_id}/cancel`

## Setup

- Postgres DB `ridedb` (created by entrypoint if missing).
- `INTERNAL_API_KEY` in env (same as realtime-service) for service-to-service auth.
- Migrations: `alembic upgrade head` (or use entrypoint).

## Vehicle types

Defined in `app/schemas/ride.py`: `bike`, `car`, `auto`, `premium_car`. Must match driver-service.
