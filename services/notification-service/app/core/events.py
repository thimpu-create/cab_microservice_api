"""
Event handlers for application lifecycle.
"""
import logging

logger = logging.getLogger(__name__)


async def on_startup():
    """
    Startup event handler.
    Initialize Firebase and other services.
    """
    logger.info("🚀 Notification Service is starting up...")
    try:
        from app.core.firebase import initialize_firebase
        initialize_firebase()
        logger.info("✅ Firebase initialized on startup")
    except Exception as e:
        logger.error(f"❌ Error initializing Firebase on startup: {e}")
        raise


async def on_shutdown():
    """
    Shutdown event handler.
    Clean up resources.
    """
    logger.info("🛑 Notification Service is shutting down...")
    try:
        import firebase_admin
        if firebase_admin._apps:
            for app in firebase_admin._apps.values():
                firebase_admin.delete_app(app)
            logger.info("✅ Firebase cleanup completed")
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")
