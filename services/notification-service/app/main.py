from fastapi import FastAPI

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
