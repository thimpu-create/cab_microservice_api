from fastapi import FastAPI
from app.api.v1 import pricing, admin, company, internal

app = FastAPI(title="Pricing Service", version="1.0.0")

# Include routers
app.include_router(pricing.router)
app.include_router(admin.router)
app.include_router(company.router)
app.include_router(internal.router)


@app.get("/health")
def health():
    return {"status": "pricing-service running"}


@app.get("/info")
def info():
    return {"service": "pricing-service", "version": "1.0.0"}


@app.get("/api/v1")
def root():
    return {"message": "Pricing Service API v1"}
