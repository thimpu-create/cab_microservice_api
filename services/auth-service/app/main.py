from fastapi import FastAPI
from .api.v1.auth import router as auth_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Auth Service", version="1.0.0")
@app.get("/health")
def health():
    return {"status": "auth-service running"}

@app.get("/info")
def info():
    return {"service": "auth-service", "version": "1.0.0"}

@app.get("/api/v1")
def root():
    return {"message": "Auth Service API v1"}

app.include_router(auth_router, prefix="/api/v1")
