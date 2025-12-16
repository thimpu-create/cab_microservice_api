from fastapi import FastAPI

app = FastAPI(title="Realtime Service", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "realtime-service running"}

@app.get("/info")
def info():
    return {"service": "realtime-service", "version": "1.0.0"}

@app.get("/api/v1")
def root():
    return {"message": "Realtime Service API v1"}
