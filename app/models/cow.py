from sqlmodel import SQLModel, Field
from typing import ClassVar, Optional
from datetime import date


class Cow(SQLModel, table=True):
    """SQLModel for Cows table"""
    __tablename__: ClassVar[str] = "Cows"
    
    id: str = Field(primary_key=True)
    name: str
    birthdate: date


class Sensor(SQLModel, table=True):
    """SQLModel for Sensors table"""
    __tablename__: ClassVar[str] = "Sensors"
    
    id: str = Field(primary_key=True)
    unit: str
