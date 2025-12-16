from fastapi import FastAPI

app = FastAPI(title="Driver Service", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "driver-service running"}

@app.get("/info")
def info():
    return {"service": "driver-service", "version": "1.0.0"}

@app.get("/api/v1")
def root():
    return {"message": "Driver Service API v1"}
