from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Import Firebase service to initialize it
from app.core.firebase import FirebaseService, initialize_firebase
from app.core.config import settings
from app.api.v1.notifications import router as notifications_router
from app.db.database import init_db
from app.core.events import on_startup, on_shutdown

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Firebase
try:
    initialize_firebase()
    logger.info("✅ Firebase initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize Firebase: {e}")

# Initialize Database
try:
    init_db()
    logger.info("✅ Database initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize database: {e}")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    """Health check endpoint."""
    return {
        "status": "notification-service running",
        "service": "notification-service",
        "version": settings.APP_VERSION
    }

@app.get("/info")
def info():
    """Service information endpoint."""
    return {
        "service": "notification-service",
        "version": settings.APP_VERSION,
        "firebase_project": settings.FIREBASE_PROJECT_ID
    }

@app.get("/api/v1")
def root():
    """API root endpoint."""
    return {
        "message": "Notification Service API v1",
        "endpoints": {
            "health": "/health",
            "info": "/info",
            "notifications": "/api/v1/notifications"
        }
    }

# Include routers
app.include_router(notifications_router, prefix="/api/v1")

from app.api.v1.devices import router as devices_router
app.include_router(devices_router, prefix="/api/v1")

logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} started")
