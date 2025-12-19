from urllib import response
from fastapi import APIRouter, HTTPException
import httpx

router = APIRouter(prefix="/company", tags=["Company"])

COMPANY_SERVICE_URL = "http://company-service:8002/api/v1/company"
# AUTH_SERVICE_URL = "http://localhost:8000/api/v1/auth"


@router.post("/register")
async def register_company():
    return {"message": "Register company endpoint - to be implemented"}