from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class MeasurementResponse(BaseModel):
    """Schema for measurement response"""
    cow_id: str
    sensor_id: str
    timestamp: float
    measured_at: datetime
    value: float
    unit: Optional[str] = None
    name: Optional[str] = None
    birthdate: Optional[date] = None
