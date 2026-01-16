from fastapi import FastAPI, HTTPException
from .api.v1.auth import router as auth_router
from .api.v1.company import router as company_router
from .api.v1.driver import router as driver_router
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="API Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "api-gateway running"}

@app.get("/info")
def info():
    return {"service": "api-gateway", "version": "1.0.0"}

@app.get("/")
def root():
    return {"message": "API Gateway Entry Point"}

app.include_router(auth_router, prefix="/api/v1")
app.include_router(company_router, prefix="/api/v1")
app.include_router(driver_router, prefix="/api/v1")

