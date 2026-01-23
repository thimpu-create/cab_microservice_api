# Pricing Engine Architecture

## Overview
Enterprise-grade pricing engine for ride-hailing platform with dynamic surge pricing, multi-vehicle support, and regulatory compliance.

## Core Concepts

### 1. Vehicle Types (from driver-service)
- `bike` - Motorcycle/Scooter
- `auto` - Auto-rickshaw
- `car` - Standard car
- `premium_car` - Luxury/premium vehicle

### 2. Pricing Components

#### Base Components:
- **Base Fare**: Fixed charge per ride
- **Per-Kilometer Rate**: Cost per km traveled
- **Per-Minute Rate**: Cost per minute of ride duration
- **Minimum Fare**: Minimum charge regardless of distance/time

#### Dynamic Components:
- **Surge Multiplier**: Dynamic multiplier based on demand/supply (1.0x to max_surge)
- **Peak Hours Multiplier**: Additional multiplier during peak hours (1.0x to peak_multiplier)

#### Constraints:
- **Regulatory Caps**: Maximum fare allowed per city/state
- **Minimum Fare**: Enforced minimum

## Database Schema

### 1. PricingProfile
Stores base pricing rules per vehicle type per city:
- city_code (e.g., "MUM", "DEL", "BLR")
- vehicle_type (bike, auto, car, premium_car)
- base_fare
- per_km_rate
- per_minute_rate
- minimum_fare
- is_active
- effective_from, effective_to (for time-based pricing)

### 2. PeakHours
Defines peak hours per city:
- city_code
- day_of_week (0-6, or "all")
- start_time, end_time
- multiplier (e.g., 1.2x during peak)
- is_active

### 3. SurgeConfig
Surge calculation parameters per vehicle type:
- vehicle_type
- base_demand_threshold (demand/supply ratio to start surge)
- max_surge_multiplier (e.g., 3.0x max)
- surge_increment (how much surge increases per demand unit)
- is_active

### 4. RegulatoryCap
Maximum fare caps per city/state:
- city_code / state_code
- vehicle_type
- max_fare_amount
- effective_from, effective_to
- is_active

### 5. PricingCalculation
Audit log of all pricing calculations:
- request_id
- user_id
- vehicle_type
- city_code
- pickup_lat, pickup_lon
- dropoff_lat, dropoff_lon
- distance_km, duration_minutes
- base_fare, distance_cost, time_cost
- surge_multiplier, peak_multiplier
- subtotal, final_fare
- calculated_at

## Pricing Flow

```
1. Input: pickup_location, dropoff_location, vehicle_type, city_code
   ↓
2. Calculate distance (km) and estimated duration (minutes)
   ↓
3. Get PricingProfile for vehicle_type + city_code
   ↓
4. Calculate base components:
   - base_fare
   - distance_cost = distance_km × per_km_rate
   - time_cost = duration_minutes × per_minute_rate
   ↓
5. Check if peak hours → apply peak_multiplier
   ↓
6. Calculate surge multiplier:
   - Get available drivers from Redis (realtime-service)
   - Get pending ride requests from Redis
   - Calculate demand/supply ratio
   - Apply surge formula based on SurgeConfig
   ↓
7. Calculate subtotal:
   subtotal = (base_fare + distance_cost + time_cost) × peak_multiplier × surge_multiplier
   ↓
8. Apply minimum fare constraint
   ↓
9. Apply regulatory cap constraint
   ↓
10. Return detailed breakdown
```

## Surge Calculation Algorithm

```
demand = count(pending_ride_requests in area)
supply = count(available_drivers in area)

demand_supply_ratio = demand / max(supply, 1)

if demand_supply_ratio < base_demand_threshold:
    surge_multiplier = 1.0
else:
    excess_demand = demand_supply_ratio - base_demand_threshold
    surge_multiplier = 1.0 + (excess_demand × surge_increment)
    surge_multiplier = min(surge_multiplier, max_surge_multiplier)
```

## API Endpoints

### Pricing:
- `POST /api/v1/pricing/calculate` - Calculate fare
- `GET /api/v1/pricing/history/{request_id}` - Get pricing calculation details

### Configuration (Admin):
- `GET /api/v1/pricing/profiles` - List pricing profiles
- `POST /api/v1/pricing/profiles` - Create pricing profile
- `PUT /api/v1/pricing/profiles/{id}` - Update pricing profile
- `GET /api/v1/pricing/surge-config` - Get surge config
- `PUT /api/v1/pricing/surge-config` - Update surge config
- `GET /api/v1/pricing/peak-hours` - List peak hours
- `POST /api/v1/pricing/peak-hours` - Create peak hours
- `GET /api/v1/pricing/regulatory-caps` - List regulatory caps
- `POST /api/v1/pricing/regulatory-caps` - Create regulatory cap

## Integration Points

1. **Redis (realtime-service)**:
   - Get available drivers: `SMEMBERS available_drivers`
   - Get driver locations: `GEORADIUS drivers_geo`
   - Get pending requests: `SCAN ride_request:*`

2. **Geo Service** (optional):
   - City detection from coordinates
   - Distance calculation (or use Haversine formula)

3. **Driver Service**:
   - Validate vehicle types
   - Get vehicle type enum

## Configuration

### Environment Variables:
```env
# Redis (for surge calculation)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Database
DATABASE_URL=postgresql://postgres:password@postgres:5432/pricingdb

# JWT
SECRET_KEY=your-secret-key
ALGORITHM=HS256

# Default surge parameters (can be overridden in DB)
DEFAULT_BASE_DEMAND_THRESHOLD=1.5
DEFAULT_MAX_SURGE=3.0
DEFAULT_SURGE_INCREMENT=0.2
```

## Example Calculation

**Input:**
```json
{
  "pickup_lat": 19.0760,
  "pickup_lon": 72.8777,
  "dropoff_lat": 19.2183,
  "dropoff_lon": 72.9781,
  "vehicle_type": "car",
  "city_code": "MUM",
  "estimated_distance_km": 15.5,
  "estimated_duration_minutes": 25
}
```

**Pricing Profile (car, MUM):**
- base_fare: 50
- per_km_rate: 12
- per_minute_rate: 1.5
- minimum_fare: 80

**Calculation:**
- base_fare = 50
- distance_cost = 15.5 × 12 = 186
- time_cost = 25 × 1.5 = 37.5
- subtotal = 50 + 186 + 37.5 = 273.5

**Peak Hours Check:**
- Current time: 18:00 (peak hours 17:00-20:00)
- peak_multiplier = 1.2
- subtotal = 273.5 × 1.2 = 328.2

**Surge Calculation:**
- Available drivers: 5
- Pending requests: 12
- demand/supply = 12/5 = 2.4
- base_threshold = 1.5
- excess = 2.4 - 1.5 = 0.9
- surge = 1.0 + (0.9 × 0.2) = 1.18
- max_surge = 3.0, so surge = 1.18
- subtotal = 328.2 × 1.18 = 387.28

**Apply Constraints:**
- Minimum fare: 80 (already exceeded)
- Regulatory cap: 500 (not exceeded)
- **Final fare = 387.28**

**Output:**
```json
{
  "base_fare": 50,
  "distance_cost": 186,
  "time_cost": 37.5,
  "subtotal": 273.5,
  "peak_multiplier": 1.2,
  "peak_adjusted_subtotal": 328.2,
  "surge_multiplier": 1.18,
  "surge_adjusted_subtotal": 387.28,
  "minimum_fare": 80,
  "regulatory_cap": 500,
  "final_fare": 387.28,
  "currency": "INR",
  "breakdown": {
    "base": 50,
    "distance": 186,
    "time": 37.5,
    "peak_surcharge": 54.7,
    "surge_surcharge": 59.08
  }
}
```
