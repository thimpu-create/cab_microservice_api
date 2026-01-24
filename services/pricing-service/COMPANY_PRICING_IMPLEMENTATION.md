# Company-Based Pricing Implementation

## ✅ Completed Updates

### 1. **Database Models Updated**
All pricing models now support `company_id`:
- `PricingProfile` - `company_id` (NULL = platform, NOT NULL = company)
- `PeakHours` - `company_id` (NULL = platform, NOT NULL = company)
- `SurgeConfig` - `company_id` (NULL = platform, NOT NULL = company) + unique constraint on (company_id, vehicle_type)
- `RegulatoryCap` - `company_id` (NULL = platform, NOT NULL = company)
- `PricingCalculation` - Added `driver_id` and `company_id` for audit trail

### 2. **Pricing Engine Updated**
- `calculate_fare()` now accepts `driver_id` and `company_id`
- Automatically fetches `company_id` from driver-service if `driver_id` provided
- Uses appropriate pricing based on `company_id`:
  - `company_id = NULL` → Platform pricing (independent drivers)
  - `company_id = NOT NULL` → Company pricing (company drivers)

### 3. **API Endpoints**

#### Admin Endpoints (Platform Pricing):
- `GET /api/v1/admin/pricing/profiles` - List platform pricing (company_id = NULL)
- `POST /api/v1/admin/pricing/profiles` - Create platform pricing
- `PUT /api/v1/admin/pricing/profiles/{id}` - Update platform pricing
- `GET /api/v1/admin/pricing/surge-config` - List platform surge configs
- `PUT /api/v1/admin/pricing/surge-config/{vehicle_type}` - Update platform surge config

#### Company Endpoints (Company Pricing):
- `GET /api/v1/company/pricing/profiles` - List company pricing (VendorAdmin only)
- `POST /api/v1/company/pricing/profiles` - Create company pricing
- `PUT /api/v1/company/pricing/profiles/{id}` - Update company pricing
- `DELETE /api/v1/company/pricing/profiles/{id}` - Deactivate company pricing
- `GET /api/v1/company/pricing/surge-config` - List company surge configs
- `PUT /api/v1/company/pricing/surge-config/{vehicle_type}` - Update company surge config

#### Pricing Calculation:
- `POST /api/v1/pricing/calculate` - Calculate fare (automatically detects driver type)

### 4. **Integration**
- **Driver Service**: Updated to return `company_id` in driver info endpoint
- **Company Service**: Added endpoint `GET /api/v1/companies/owned-by/{user_id}` to get company for VendorAdmin
- **Company Client**: Fetches company_id for VendorAdmin users
- **Driver Info Client**: Fetches company_id for drivers

## 🔄 Pricing Flow

```
1. Calculate Fare Request (with driver_id)
   ↓
2. Get driver info from driver-service → get company_id
   ↓
3. If company_id = NULL:
   → Use platform pricing (admin-managed)
   ↓
4. If company_id = NOT NULL:
   → Use company pricing (company-managed)
   ↓
5. Apply pricing rules (base, distance, time, peak, surge, constraints)
   ↓
6. Return fare breakdown
```

## 📋 Authorization

- **Admin**: Can manage platform pricing only (company_id = NULL)
- **VendorAdmin**: Can manage their company's pricing only (company_id = their_company_id)
- Companies can only access/modify their own pricing

## 🎯 Usage Examples

### Calculate Fare (Independent Driver):
```json
POST /api/v1/pricing/calculate
{
  "pickup_lat": 19.0760,
  "pickup_lon": 72.8777,
  "dropoff_lat": 19.2183,
  "dropoff_lon": 72.9781,
  "vehicle_type": "car",
  "city_code": "MUM",
  "driver_id": "uuid-of-independent-driver"  // company_id will be NULL
}
```
→ Uses platform pricing (admin-managed)

### Calculate Fare (Company Driver):
```json
POST /api/v1/pricing/calculate
{
  "pickup_lat": 19.0760,
  "pickup_lon": 72.8777,
  "dropoff_lat": 19.2183,
  "dropoff_lon": 72.9781,
  "vehicle_type": "car",
  "city_code": "MUM",
  "driver_id": "uuid-of-company-driver"  // company_id will be fetched
}
```
→ Uses company pricing (company-managed)

### Admin Creates Platform Pricing:
```json
POST /api/v1/admin/pricing/profiles
Authorization: Bearer <admin-token>
{
  "city_code": "MUM",
  "vehicle_type": "car",
  "base_fare": 50,
  "per_km_rate": 12,
  "per_minute_rate": 1.5,
  "minimum_fare": 80
}
```
→ Creates pricing with `company_id = NULL`

### VendorAdmin Creates Company Pricing:
```json
POST /api/v1/company/pricing/profiles
Authorization: Bearer <vendoradmin-token>
{
  "city_code": "MUM",
  "vehicle_type": "car",
  "base_fare": 60,  // Company can set different rates
  "per_km_rate": 15,
  "per_minute_rate": 2.0,
  "minimum_fare": 100
}
```
→ Creates pricing with `company_id = <their_company_id>`

## ✅ Next Steps

1. Create database: `docker exec postgres psql -U postgres -c "CREATE DATABASE pricingdb;"`
2. Run migrations to add `company_id` columns
3. Seed initial platform pricing profiles
4. Test with both independent and company drivers
