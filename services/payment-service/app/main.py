from fastapi import FastAPI

app = FastAPI(title="Payment Service", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "payment-service running"}

@app.get("/info")
def info():
    return {"service": "payment-service", "version": "1.0.0"}

@app.get("/api/v1")
def root():
    return {"message": "Payment Service API v1"}
