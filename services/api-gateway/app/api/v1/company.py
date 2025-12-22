from urllib import response
from fastapi import APIRouter, HTTPException, Depends
import httpx
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="/company", tags=["Company"])

COMPANY_SERVICE_URL = "http://company-service:8002/api/v1/company"
# AUTH_SERVICE_URL = "http://localhost:8000/api/v1/auth"

security = HTTPBearer()

@router.post("/register")
async def register_company(credentials: HTTPAuthorizationCredentials = Depends(security),payload: dict = None):
    return {"message": "Register company endpoint - to be implemented"}