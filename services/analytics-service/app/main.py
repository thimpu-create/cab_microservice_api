from fastapi import FastAPI

app = FastAPI(title="Analytics Service", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "analytics-service running"}

@app.get("/info")
def info():
    return {"service": "analytics-service", "version": "1.0.0"}

@app.get("/api/v1")
def root():
    return {"message": "Analytics Service API v1"}
