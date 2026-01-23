from fastapi import FastAPI
from app.api.v1 import sos, contacts, emergency_number

app = FastAPI(title="SOS Service", version="1.0.0")

# Include routers
app.include_router(sos.router)
app.include_router(contacts.router)
app.include_router(emergency_number.router)


@app.get("/health")
def health():
    return {"status": "sos-service running"}


@app.get("/info")
def info():
    return {"service": "sos-service", "version": "1.0.0"}


@app.get("/api/v1")
def root():
    return {"message": "SOS Service API v1"}
