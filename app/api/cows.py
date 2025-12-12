from fastapi import APIRouter, HTTPException
from app.schemas.cow import CowCreate, CowResponse
from app.services.cow_service import CowService

router = APIRouter()
cow_service = CowService()

@router.post("/{id}", response_model=CowResponse, status_code=201)
async def create_cow(id: str, cow: CowCreate):
    """Create a new cow"""
    try:
        return await cow_service.create_cow(id, cow)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.get("/{id}", response_model=CowResponse)
async def get_cow(id: str):
    """Get cow by ID"""
    cow = await cow_service.get_cow(id)
    if not cow:
        raise HTTPException(status_code=404, detail=f"Cow with id {id} not found")
    return cow

@router.get("/", response_model=list[CowResponse])
async def list_cows():
    """List all cows"""
    return await cow_service.list_cows()
