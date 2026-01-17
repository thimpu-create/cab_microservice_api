# Testing Company Driver Registration

## Endpoint

```
POST /api/v1/drivers/company/{company_id}/register
```

**Requires:** Authentication (Bearer Token)

## Two Registration Modes

### Mode 1: Register Existing User as Driver

If the user already has an account, provide their `user_id`.

### Mode 2: Create New User + Register as Driver

If the user doesn't exist, provide user details and the system will create the account automatically.

---

## Test Examples

### Example 1: Register New User as Company Driver (Mode 2)

**Endpoint:**
```
POST http://localhost:8000/api/v1/drivers/company/{company_id}/register
```

**Headers:**
```
Authorization: Bearer <your_jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "fname": "John",
  "lname": "Driver",
  "email": "john.driver@company.com",
  "phone": "+1234567890",
  "password": "SecurePass123!",
  "license_number": "DL123456",
  "license_expiry_date": "2025-12-31T00:00:00",
  "license_state_province": "California",
  "vehicle_make": "Toyota",
  "vehicle_model": "Camry",
  "vehicle_year": 2020,
  "vehicle_color": "Blue",
  "vehicle_plate_number": "ABC-1234",
  "notes": "Experienced driver with 5 years of service"
}
```

**cURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/drivers/company/YOUR_COMPANY_ID/register" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fname": "John",
    "lname": "Driver",
    "email": "john.driver@company.com",
    "phone": "+1234567890",
    "password": "SecurePass123!",
    "license_number": "DL123456",
    "vehicle_make": "Toyota",
    "vehicle_model": "Camry",
    "vehicle_year": 2020,
    "vehicle_color": "Blue",
    "vehicle_plate_number": "ABC-1234"
  }'
```

---

### Example 2: Register Existing User as Company Driver (Mode 1)

**Request Body:**
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "license_number": "DL789012",
  "license_expiry_date": "2026-06-30T00:00:00",
  "license_state_province": "New York",
  "vehicle_make": "Honda",
  "vehicle_model": "Accord",
  "vehicle_year": 2021,
  "vehicle_color": "White",
  "vehicle_plate_number": "XYZ-5678",
  "notes": "Part-time driver"
}
```

**cURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/drivers/company/YOUR_COMPANY_ID/register" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "license_number": "DL789012",
    "vehicle_make": "Honda",
    "vehicle_model": "Accord",
    "vehicle_year": 2021,
    "vehicle_color": "White",
    "vehicle_plate_number": "XYZ-5678"
  }'
```

---

### Example 3: Minimal Required Fields (Mode 2)

**Request Body:**
```json
{
  "fname": "Jane",
  "lname": "Smith",
  "email": "jane.smith@company.com",
  "phone": "+1987654321",
  "password": "SecurePass123!"
}
```

**Note:** All driver-specific fields (license, vehicle info) are optional.

---

## Field Descriptions

### Required for Mode 2 (New User):
- `fname` - First name
- `lname` - Last name
- `email` - Email address (must be unique)
- `phone` - Phone number (must be unique)
- `password` - Password for user account

### Required for Mode 1 (Existing User):
- `user_id` - UUID of existing user

### Optional Fields (All Modes):
- `mname` - Middle name
- `license_number` - Driver's license number
- `license_expiry_date` - License expiration date (ISO format)
- `license_state_province` - State/Province of license
- `vehicle_make` - Vehicle manufacturer
- `vehicle_model` - Vehicle model
- `vehicle_year` - Vehicle year
- `vehicle_color` - Vehicle color
- `vehicle_plate_number` - License plate number
- `notes` - Additional notes

---

## Response Example

**Success (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "company_id": "987fcdeb-51a2-43f7-8b9c-123456789abc",
  "license_number": "DL123456",
  "license_expiry_date": "2025-12-31T00:00:00",
  "license_state_province": "California",
  "vehicle_make": "Toyota",
  "vehicle_model": "Camry",
  "vehicle_year": 2020,
  "vehicle_color": "Blue",
  "vehicle_plate_number": "ABC-1234",
  "notes": "Experienced driver with 5 years of service",
  "status": "pending_verification",
  "is_verified": false,
  "is_active": true,
  "created_at": "2024-01-16T12:00:00Z",
  "updated_at": null
}
```

---

## Error Responses

### Missing Required Fields (400):
```json
{
  "detail": "If user_id is not provided, you must provide: fname, lname, email, phone, password"
}
```

### Duplicate Email/Phone (400):
```json
{
  "detail": "Failed to create user account: Email or phone already registered"
}
```

### Driver Already Exists (409):
```json
{
  "detail": "Driver already registered for this user"
}
```

### Unauthorized (401):
```json
{
  "detail": "Not authenticated"
}
```

---

## Quick Test Steps

1. **Get JWT Token:**
   ```bash
   POST http://localhost:8000/api/v1/auth/login
   {
     "email": "your_email@example.com",
     "password": "your_password"
   }
   ```

2. **Get Company ID:**
   - From your company registration or database

3. **Register Driver:**
   ```bash
   POST http://localhost:8000/api/v1/drivers/company/{company_id}/register
   Authorization: Bearer {jwt_token}
   {
     "fname": "Test",
     "lname": "Driver",
     "email": "test.driver@company.com",
     "phone": "+1555123456",
     "password": "Test123!",
     "license_number": "DL999888"
   }
   ```

---

## Notes

- The endpoint automatically creates a user account in auth-service if `user_id` is not provided
- The user will be created with the "VendorDriver" role (for company drivers)
- The driver status will be set to `pending_verification` by default
- All driver-specific fields are optional - you can register with just user info and add vehicle details later
