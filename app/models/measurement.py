from sqlmodel import SQLModel, Field
from typing import ClassVar, Optional
from datetime import date, datetime


class Measurement(SQLModel, table=True):
    """SQLModel for Measurements table"""
    __tablename__: ClassVar[str] = "Measurements"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    cow_id: str = Field(index=True)
    sensor_id: str
    timestamp: float
    measured_at: datetime
    value: float
    unit: Optional[str] = None
    name: Optional[str] = None
    birthdate: Optional[date] = None
    recorded_at: datetime = Field(default_factory=datetime.utcnow)
