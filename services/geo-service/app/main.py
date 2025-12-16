from fastapi import FastAPI

app = FastAPI(title="Geo Service", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "geo-service running"}

@app.get("/info")
def info():
    return {"service": "geo-service", "version": "1.0.0"}

@app.get("/api/v1")
def root():
    return {"message": "Geo Service API v1"}
