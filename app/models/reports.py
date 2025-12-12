from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List


class CowWeightReport(BaseModel):
    """Schema for cow weight report"""
    cow_id: str
    cow_name: str
    current_weight: Optional[float]
    current_weight_date: Optional[datetime]
    avg_weight_30_days: Optional[float]
    measurements_30_days: int
    ill: bool = False


class MeasurementDetail(BaseModel):
    """Schema for individual measurement detail"""
    cow_id: str
    cow_name: str
    value: float
    measured_at: datetime
    sensor_id: str


class DailyMilkReport(BaseModel):
    """Schema for daily milk production report"""
    date: date
    total_liters: float
    measurement_count: int
    measurements: List[MeasurementDetail]


class MilkSummaryReport(BaseModel):
    """Schema for overall milk production summary"""
    total_liters: float
    total_measurements: int
    avg_per_measurement: float
    first_measurement: Optional[datetime]
    last_measurement: Optional[datetime]