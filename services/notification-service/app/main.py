from fastapi import FastAPI
from .api.v1.notifications import router as notifications_router
from .api.v1.devices import router as devices_router

app = FastAPI(title="Notification Service", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "notification-service running"}

@app.get("/info")
def info():
    return {"service": "notification-service", "version": "1.0.0"}

@app.get("/api/v1")
def root():
    return {"message": "Notification Service API v1"}

app.include_router(notifications_router, prefix="/api/v1")
app.include_router(devices_router, prefix="/api/v1")
