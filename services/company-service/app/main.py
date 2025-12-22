from fastapi import FastAPI
from .api.v1.company import router as companies_router

app = FastAPI(title="Company Service", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "company-service running"}

@app.get("/info")
def info():
    return {"service": "company-service", "version": "1.0.0"}

@app.get("/api/v1")
def root():
    return {"message": "Company Service API v1"}

app.include_router(companies_router)
