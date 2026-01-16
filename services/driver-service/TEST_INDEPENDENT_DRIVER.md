# Testing Independent Driver Registration

## ✅ **NO NEED TO CREATE AUTH ACCOUNT FIRST!**

The `/register/independent` endpoint **automatically creates both**:
1. User account in auth-service (with "IndependentDriver" role)
2. Driver profile in driver-service (with `company_id = null`)

## 🚀 **Single API Call - Everything is Done Automatically**

### **Option 1: Via API Gateway (Recommended)**

```bash
POST http://localhost:8000/api/v1/drivers/register/independent
Content-Type: application/json

{
  "fname": "John",
  "lname": "Doe",
  "email": "john.driver@example.com",
  "phone": "+1234567890",
  "password": "SecurePass123!",
  "license_number": "DL123456",
  "vehicle_make": "Toyota",
  "vehicle_model": "Camry",
  "vehicle_year": 2020,
  "vehicle_color": "Blue",
  "vehicle_plate_number": "ABC-1234"
}
```

### **Option 2: Direct to Driver Service**

```bash
POST http://localhost:8003/api/v1/drivers/register/independent
Content-Type: application/json

{
  "fname": "Jane",
  "lname": "Smith",
  "email": "jane.driver@example.com",
  "phone": "+1987654321",
  "password": "SecurePass123!",
  "license_number": "DL789012"
}
```

## 📋 **Required Fields**

- `fname` (first name)
- `lname` (last name)
- `email` (must be unique)
- `phone` (must be unique)
- `password`

## 📋 **Optional Fields**

- `mname` (middle name)
- `license_number`
- `license_expiry_date`
- `license_state_province`
- `vehicle_make`
- `vehicle_model`
- `vehicle_year`
- `vehicle_color`
- `vehicle_plate_number`
- `notes`

## 🔄 **What Happens Behind the Scenes**

1. **Driver Service** receives the request
2. **Driver Service** calls **Auth Service** to create user account:
   - Creates user with "IndependentDriver" role
   - Returns user UUID
3. **Driver Service** creates driver profile:
   - Links to user UUID
   - Sets `company_id = null` (independent driver)
   - Sets status to `pending_verification`
4. Returns complete driver profile

## ✅ **Response Example**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "company_id": null,
  "license_number": "DL123456",
  "vehicle_make": "Toyota",
  "vehicle_model": "Camry",
  "vehicle_year": 2020,
  "vehicle_color": "Blue",
  "vehicle_plate_number": "ABC-1234",
  "status": "pending_verification",
  "is_verified": false,
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": null
}
```

## 🔐 **After Registration**

You can now **login** using the email/phone and password:

```bash
POST http://localhost:8000/api/v1/auth/login
Content-Type: application/json

{
  "email": "john.driver@example.com",
  "password": "SecurePass123!"
}
```

## ⚠️ **Error Cases**

### **Duplicate Email/Phone**
```json
{
  "detail": "Failed to create user account: Email or phone already registered"
}
```

### **Missing Required Fields**
```json
{
  "detail": "Required fields: fname, lname, email, phone, password"
}
```

### **Driver Already Exists**
If you try to register again with the same user:
```json
{
  "detail": "Driver already registered for this user"
}
```

## 🧪 **Quick Test with cURL**

```bash
curl -X POST http://localhost:8000/api/v1/drivers/register/independent \
  -H "Content-Type: application/json" \
  -d '{
    "fname": "Test",
    "lname": "Driver",
    "email": "test.driver@example.com",
    "phone": "+1555123456",
    "password": "Test123!",
    "license_number": "TEST123"
  }'
```

## 📝 **Summary**

✅ **One API call** creates everything  
✅ **No need** to create auth account separately  
✅ **Automatic** user account creation  
✅ **Automatic** driver profile creation  
✅ **Ready to login** immediately after registration
