# backend/src/api/routes/pack.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from ..dependencies import get_pack_service
from ..schemas import PackCreateRequest, PackResponse, PackListResponse
from ...services.pack_service import PackService
from ...models.pack import CreatorType
from ...utils import ensure_uuid

router = APIRouter()

@router.post("/", response_model=PackResponse, status_code=201)
async def create_pack(
    pack_data: PackCreateRequest,
    pack_service: PackService = Depends(get_pack_service)
):
    """
    Create a new trivia pack.
    
    Args:
        pack_data: Data for creating the pack
        pack_service: Pack service dependency
        
    Returns:
        Newly created pack
    """
    # Check if a pack with this name already exists
    exists, existing_id = await pack_service.validate_creation_name(pack_data.name)
    
    if exists:
        raise HTTPException(
            status_code=400,
            detail=f"A pack with the name '{pack_data.name}' already exists"
        )
    
    # Create the pack
    pack, _ = await pack_service.get_or_create_pack(
        pack_name=pack_data.name,
        pack_description=pack_data.description,
        price=pack_data.price,
        creator_type=pack_data.creator_type
    )
    
    return pack

@router.get("/", response_model=PackListResponse)
async def list_packs(
    skip: int = Query(0, ge=0, description="Number of packs to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of packs to return"),
    creator_type: Optional[CreatorType] = Query(None, description="Filter by creator type"),
    search: Optional[str] = Query(None, description="Search by pack name"),
    pack_service: PackService = Depends(get_pack_service)
):
    """
    List all packs with optional filtering.
    
    Args:
        skip: Number of packs to skip (pagination)
        limit: Number of packs to return (pagination)
        creator_type: Optional filter by creator type
        search: Optional search by pack name
        pack_service: Pack service dependency
        
    Returns:
        List of packs matching the criteria
    """
    # This endpoint would require implementation in the pack_service
    # For now, returning a placeholder implementation
    
    raise HTTPException(
        status_code=501,
        detail="This endpoint is not implemented yet"
    )

@router.get("/{pack_id}", response_model=PackResponse)
async def get_pack(
    pack_id: str,
    pack_service: PackService = Depends(get_pack_service)
):
    """
    Get a specific pack by ID.
    
    Args:
        pack_id: ID of the pack to retrieve
        pack_service: Pack service dependency
        
    Returns:
        Pack details
    """
    # Ensure pack_id is a valid UUID string
    pack_id = ensure_uuid(pack_id)
    
    # This endpoint would require implementation in the pack_service
    # to get a pack by ID from the repository
    
    raise HTTPException(
        status_code=501,
        detail="This endpoint is not implemented yet"
    )