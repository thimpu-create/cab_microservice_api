from fastapi import APIRouter, HTTPException
import httpx
from generated.auth_models.openapi_client.models.login_schema import LoginSchema
from generated.auth_models.openapi_client.models.user_create import UserCreate

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

@router.post("/register")
async def register(payload: UserCreate):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{AUTH_SERVICE_URL}/register", json=payload.model_dump())
        except Exception:
            raise HTTPException(status_code=500, detail="Auth service unavailable")

    if response.status_code != 200:
        print("response not 200", response.status_code, response.json())
        raise HTTPException(status_code=response.status_code, detail=response.json().get("detail"))

    return response.json()