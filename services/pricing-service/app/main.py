from fastapi import FastAPI

app = FastAPI(title="Pricing Service", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "pricing-service running"}

@app.get("/info")
def info():
    return {"service": "pricing-service", "version": "1.0.0"}

@app.get("/api/v1")
def root():
    return {"message": "Pricing Service API v1"}
