from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api import cows, measurements, reports
from app.core.config import settings
import logging

from app.database import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

# Suppress watchfiles logs
logging.getLogger('watchfiles').setLevel(logging.WARNING)

# Create a logger instance
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting up {settings.PROJECT_NAME} v{settings.VERSION}")
    app.state.db = Database()
    app.state.db.init_database()
    yield
    # Shutdown
    logger.info("Shutting down IngFarm API")
    app.state.db.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="IngFarm API for managing cows and measurements",
    lifespan=lifespan
)

# Include routers
app.include_router(cows.router, prefix="/api/v1/cows", tags=["cows"])
app.include_router(measurements.router, prefix="/api/v1/measurements", tags=["measurements"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])

@app.get("/")
async def root():
    return {"message": "Welcome to IngFarm API", "version": settings.VERSION}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
