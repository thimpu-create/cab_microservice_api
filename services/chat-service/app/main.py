from fastapi import FastAPI

app = FastAPI(title="Chat Service", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "chat-service running"}

@app.get("/info")
def info():
    return {"service": "chat-service", "version": "1.0.0"}

@app.get("/api/v1")
def root():
    return {"message": "Chat Service API v1"}
