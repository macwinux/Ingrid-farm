from pydantic import BaseModel
from datetime import date

class CowCreate(BaseModel):
    """Schema for creating a cow"""
    name: str
    birthdate: date

class CowResponse(BaseModel):
    """Schema for cow response"""
    id: str
    name: str
    birthdate: date
