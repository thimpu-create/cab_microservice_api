from fastapi import FastAPI

from app.api.v1 import internal

app = FastAPI(title="Ride Service", version="1.0.0")

app.include_router(internal.router, prefix="/api/v1")

@app.get("/health")
def health():
    return {"status": "ride-service running"}

@app.get("/info")
def info():
    return {"service": "ride-service", "version": "1.0.0"}

@app.get("/api/v1")
def root():
    return {"message": "Ride Service API v1"}
