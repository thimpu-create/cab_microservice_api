from fastapi import FastAPI
from .api.v1.company_driver import router as company_driver_router
from .api.v1.independent_driver import router as independent_driver_router
from .api.v1.realtime import router as realtime_router
from .api.v1.ratings import router as ratings_router
from .api.v1.driver_info import router as driver_info_router

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

# Include routers
app.include_router(company_driver_router, prefix="/api/v1")
app.include_router(independent_driver_router, prefix="/api/v1")
app.include_router(realtime_router, prefix="/api/v1")
app.include_router(ratings_router, prefix="/api/v1")
app.include_router(driver_info_router, prefix="/api/v1")
