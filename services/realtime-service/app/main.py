from fastapi import FastAPI
from contextlib import asynccontextmanager
import threading
import asyncio
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.websocket import router as websocket_router
from app.core.redis_listener import listen_to_redis
from app.api.v1.ride_request import router as ride_request_router
from app.api.v1.ride_history import router as ride_history_router
from app.core.websocket_manager import start_cleanup_task


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Start Redis pub/sub listener in background thread
    t = threading.Thread(target=listen_to_redis, daemon=True)
    t.start()
    print("✅ Realtime service started - Redis listener active")
    
    # Start WebSocket cleanup task
    cleanup_task = asyncio.create_task(start_cleanup_task())
    print("✅ WebSocket cleanup task started")
    
    yield  # App is running
    
    # Cancel cleanup task
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    
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
    from app.core.websocket_manager import ws_manager
    stats = ws_manager.get_connection_stats()
    return {
        "service": "realtime-service",
        "version": "1.0.0",
        "connections": stats
    }

@app.get("/api/v1")
def root():
    return {"message": "Realtime Service API v1"}

# Include routers
app.include_router(websocket_router)
app.include_router(ride_request_router, prefix="/api/v1")
app.include_router(ride_history_router, prefix="/api/v1")
