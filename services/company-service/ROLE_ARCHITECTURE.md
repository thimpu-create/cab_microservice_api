# Role Architecture Explanation

## 🎯 Two-Level Role System

This system uses a **two-level role architecture** to separate **user identity** from **company context**.

---

## 📊 Level 1: System Roles (Auth Service)

**Location:** `services/auth-service/`  
**Model:** `Role` (bound to `User` model)  
**Purpose:** Defines **WHO the user IS** across the entire system

### Roles Defined:
- `SuperAdmin` - System super administrator
- `AdminManager` - Admin manager
- `AdminSupport` - Admin support staff
- `VendorAdmin` - Company/vendor administrator (can create companies)
- `VendorDriver` - Driver working for a company
- `VendorManager` - Manager at a company
- `VendorSupport` - Support staff at a company
- `IndependentDriver` - Independent driver (not tied to a company)
- `User` - Regular passenger/user

### Characteristics:
- ✅ **Tightly bound to User model** - Part of user's core identity
- ✅ **Global scope** - Applies regardless of company association
- ✅ **Defines user profile** - Who they are in the system
- ✅ **Set during registration** - Determined when user account is created

### Example:
```python
# User with system role "VendorAdmin"
user = User(
    email="john@example.com",
    role_id=4  # VendorAdmin role
)
# This user IS a VendorAdmin across the entire system
```

---

## 🏢 Level 2: Company Roles (Company Service)

**Location:** `services/company-service/`  
**Model:** `CompanyUser` (junction table)  
**Enum:** `UserCompanyRole`  
**Purpose:** Defines **what role the user has WITHIN a specific company**

### Roles Defined:
- `owner` - Company owner
- `admin` - Company administrator
- `manager` - Company manager
- `dispatcher` - Dispatcher
- `support` - Support staff
- `driver` - Driver (within company)
- `accountant` - Accountant

### Characteristics:
- ✅ **Contextual** - Only applies when user is associated with a company
- ✅ **Multiple companies** - User can have different roles in different companies
- ✅ **Permissions** - Controls what user can do within that company
- ✅ **Created when user joins company** - Set when `CompanyUser` entry is created

### Example:
```python
# User is VendorAdmin (system role) AND owner of Company A
company_user = CompanyUser(
    user_id=user.uuid,
    company_id=company_a.id,
    role=UserCompanyRole.owner  # Owner role WITHIN Company A
)

# Same user can be manager of Company B
company_user_b = CompanyUser(
    user_id=user.uuid,
    company_id=company_b.id,
    role=UserCompanyRole.manager  # Manager role WITHIN Company B
)
```

---

## 🔄 How They Work Together

### Scenario 1: User Creates a Company

1. **User has system role:** `VendorAdmin` (from auth-service)
2. **User creates company:** `POST /companies/register`
3. **System automatically:**
   - Creates `CabCompany` with `owner_user_id = user.uuid`
   - Creates `CompanyUser` entry with `role = UserCompanyRole.owner`
   - Sets all permissions to `True` for owner

**Result:**
- System role: `VendorAdmin` (who they are)
- Company role: `owner` (their role in the company they created)

### Scenario 2: User Joins Existing Company

1. **User has system role:** `VendorDriver` (from auth-service)
2. **Admin adds user to company:** `POST /companies/{company_id}/users`
3. **System creates:** `CompanyUser` entry with `role = UserCompanyRole.driver`

**Result:**
- System role: `VendorDriver` (who they are)
- Company role: `driver` (their role in this specific company)

---

## 📋 Key Differences

| Aspect | System Roles (Auth) | Company Roles (Company) |
|--------|---------------------|-------------------------|
| **Scope** | Global (entire system) | Contextual (specific company) |
| **Bound to** | User model | CompanyUser junction table |
| **Purpose** | User identity/profile | Company-specific permissions |
| **Multiple values** | ❌ One per user | ✅ One per company |
| **Set when** | User registration | Company association |
| **Example** | "I am a VendorAdmin" | "I am owner of Company X" |

---

## ✅ Current Implementation

### Company Registration Flow:
```python
# 1. User creates company
POST /companies/register
→ Creates CabCompany with owner_user_id

# 2. System automatically creates CompanyUser entry
→ role = UserCompanyRole.owner
→ All permissions = True
→ is_verified = True
```

### Result:
- ✅ Owner appears in `company_users` table
- ✅ Owner has full permissions
- ✅ Owner can be queried via `/companies/{id}/users`
- ✅ Owner's system role (VendorAdmin) remains separate

---

## 🎯 Summary

- **System Roles** = User's identity/profile (WHO they are)
- **Company Roles** = User's role within a company (WHAT they can do in that company)
- **Both are needed** - System role for authentication, Company role for company-specific permissions
- **Owner is auto-created** - When company is registered, owner is automatically added to `company_users` table
