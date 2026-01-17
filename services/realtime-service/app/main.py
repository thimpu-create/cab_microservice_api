from fastapi import FastAPI
from contextlib import asynccontextmanager
import threading
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.websocket import router as websocket_router
from app.core.redis_listener import listen_to_redis
from app.api.v1.ride_request import router as ride_request_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Start Redis pub/sub listener in background thread
    t = threading.Thread(target=listen_to_redis, daemon=True)
    t.start()
    print("✅ Realtime service started - Redis listener active")
    
    yield  # App is running
    
    print("🛑 Stopping realtime service...")


app = FastAPI(
    title="Realtime Service",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "realtime-service running"}

@app.get("/info")
def info():
    return {"service": "realtime-service", "version": "1.0.0"}

@app.get("/api/v1")
def root():
    return {"message": "Realtime Service API v1"}

# Include routers
app.include_router(websocket_router)
app.include_router(ride_request_router, prefix="/api/v1")
