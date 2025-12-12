from app.schemas.measurement import MeasurementResponse
from app.services.cow_service import CowService
from simulators.read_measurements import MeasurementReader

class MeasurementService:
    """Service for measurement operations"""
    
    def __init__(self):
        self.reader = MeasurementReader()
        self.cow_service = CowService()
    
    async def get_next_measurement(self, cow_id: str) -> MeasurementResponse:
        """Get next measurement for a cow"""
        measurement = self.reader.get_next_measurement(cow_id)
        return MeasurementResponse(**measurement.model_dump())
    
    async def reset_index(self, cow_id: str):
        """Reset measurement index for a cow"""
        self.reader.reset_index(cow_id)
    
    async def get_all_cows_measurements(self) -> list[MeasurementResponse]:
        """Get current measurement for all cows"""
        cows = await self.cow_service.list_cows()
        measurements = []
        
        for cow in cows:
            try:
                measurement = self.reader.get_next_measurement(cow.id)
                measurements.append(MeasurementResponse(**measurement.model_dump()))
            except ValueError:
                # Skip cows without measurements
                continue
        
        return measurements
