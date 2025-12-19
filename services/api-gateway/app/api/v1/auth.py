from fastapi import APIRouter, HTTPException
import httpx
from generated.auth_client.openapi_client.models.login_schema import LoginSchema
from generated.auth_client.openapi_client.models.passenger_register import PassengerRegister
from generated.auth_client.openapi_client.models.vendor_admin_register import VendorAdminRegister
from generated.auth_client.openapi_client.models.independent_driver_register import IndependentDriverRegister

router = APIRouter(prefix="/auth", tags=["Auth"])

AUTH_SERVICE_URL = "http://auth-service:8000/api/v1/auth"
# AUTH_SERVICE_URL = "http://localhost:8000/api/v1/auth"


@router.post("/login")
async def login(payload: LoginSchema):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{AUTH_SERVICE_URL}/login", json=payload.model_dump())
        except Exception:
            raise HTTPException(status_code=500, detail="Auth service unavailable")

    if response.status_code != 200:
        print("response not 200", response.status_code, response.json())
        raise HTTPException(status_code=response.status_code, detail=response.json().get("detail"))

    return response.json()

@router.post("/register/passenger")
async def register_passenger(payload: PassengerRegister):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{AUTH_SERVICE_URL}/register/passenger", json=payload.model_dump())
        except Exception:
            raise HTTPException(status_code=500, detail="Auth service unavailable")

    if response.status_code != 200:
        print("response not 200", response.status_code, response.json())
        raise HTTPException(status_code=response.status_code, detail=response.json().get("detail"))

    return response.json()
@router.post("/register/vendor-admin")
async def register_vendor_admin(payload: VendorAdminRegister,):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{AUTH_SERVICE_URL}/register/vendor-admin", json=payload.model_dump())
        except Exception:
            raise HTTPException(status_code=500, detail="Auth service unavailable")

    if response.status_code != 200:
        print("response not 200", response.status_code, response.json())
        raise HTTPException(status_code=response.status_code, detail=response.json().get("detail"))

    return response.json()
@router.post("/register/independent-driver")
async def register_independent_driver(payload: IndependentDriverRegister):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{AUTH_SERVICE_URL}/register/independent-driver", json=payload.model_dump())
        except Exception:
            raise HTTPException(status_code=500, detail="Auth service unavailable")

    if response.status_code != 200:
        print("response not 200", response.status_code, response.json())
        raise HTTPException(status_code=response.status_code, detail=response.json().get("detail"))

    return response.json()