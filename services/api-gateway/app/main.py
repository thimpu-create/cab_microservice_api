from fastapi import FastAPI, HTTPException
from .api.v1.auth import router as auth_router


app = FastAPI(title="API Gateway", version="1.0.0")

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

