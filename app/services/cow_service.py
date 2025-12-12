import uuid
from typing import Optional
from sqlmodel import select
from app.schemas.cow import CowCreate, CowResponse
from app.models.cow import Cow
from app.database import get_db

class CowService:
    """Service for cow operations"""
    
    def __init__(self):
        pass
    
    async def create_cow(self, id: str, cow: CowCreate) -> CowResponse:
        """Create a new cow"""
        # Validate UUID format
        try:
            uuid.UUID(id)
        except ValueError:
            raise ValueError("Invalid UUID format")
        
        db = get_db()
        
        with db.get_session() as session:
            # Check if cow with this ID already exists
            existing_cow = session.exec(select(Cow).where(Cow.id == id)).first()
            if existing_cow:
                raise FileExistsError(f"Cow with id {id} already exists")
            
            # Create new cow
            new_cow = Cow(
                id=id,
                name=cow.name,
                birthdate=cow.birthdate
            )
            session.add(new_cow)
            session.commit()
            session.refresh(new_cow)
            
            return CowResponse(id=new_cow.id, name=new_cow.name, birthdate=new_cow.birthdate)
    
    async def get_cow(self, id: str) -> Optional[CowResponse]:
        """Get cow by ID"""
        db = get_db()
        
        with db.get_session() as session:
            cow = session.exec(select(Cow).where(Cow.id == id)).first()
            
            if not cow:
                return None
            
            return CowResponse(id=cow.id, name=cow.name, birthdate=cow.birthdate)
    
    async def list_cows(self) -> list[CowResponse]:
        """List all cows"""
        db = get_db()
        
        with db.get_session() as session:
            cows = session.exec(select(Cow)).all()
            return [CowResponse(id=cow.id, name=cow.name, birthdate=cow.birthdate) for cow in cows]
