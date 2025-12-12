from fastapi import APIRouter, HTTPException
from fastapi_utils.tasks import repeat_every
from app.schemas.measurement import MeasurementResponse
from app.services.measurement_service import MeasurementService
from app.database import get_db
import logging

logger = logging.getLogger(__name__)
db = get_db()
router = APIRouter()
measurement_service = MeasurementService()

@router.on_event("startup")
@repeat_every(seconds=60)
async def save_measurements_periodically():
    """Background task: Save measurements to database every 5 seconds"""
    try:
        measurements = await measurement_service.get_all_cows_measurements()
        if measurements:
            db.save_measurements(measurements)
            logger.info(f"Background task saved {len(measurements)} measurements")
    except Exception as e:
        logger.error(f"Error in background task: {str(e)}")

@router.get("/{cow_id}", response_model=MeasurementResponse)
async def get_next_measurement(cow_id: str):
    """Get next measurement for a cow"""
    try:
        measurement = await measurement_service.get_next_measurement(cow_id)
        if measurement:
            db.save_measurements([measurement])
        return measurement
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
