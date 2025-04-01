from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
import logging
import traceback

from ..dependencies import get_pack_service
from ..schemas import PackCreateRequest, PackResponse, PackListResponse
from ...services.pack_service import PackService
from ...models.pack import CreatorType
from ...utils import ensure_uuid

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=PackResponse, status_code=status.HTTP_201_CREATED)
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
    try:
        logger.info(f"Attempting to create pack with name: {pack_data.name}")
        
        # Check if a pack with this name already exists
        exists, existing_id = await pack_service.validate_creation_name(pack_data.name)
        
        if exists:
            logger.warning(f"Pack with name '{pack_data.name}' already exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A pack with the name '{pack_data.name}' already exists"
            )
        
        # Create the pack
        logger.info(f"Creating new pack: {pack_data.name}")
        pack, _ = await pack_service.get_or_create_pack(
            pack_name=pack_data.name,
            pack_description=pack_data.description,
            price=pack_data.price,
            creator_type=pack_data.creator_type
        )
        
        logger.info(f"Successfully created pack: {pack.name} with ID: {pack.id}")
        return pack
        
    except HTTPException:
        # Re-raise HTTP exceptions
        logger.exception("HTTP exception while creating pack")
        raise
    except Exception as e:
        # Log the full exception with traceback
        logger.error(f"Unexpected error creating pack: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create pack: {str(e)}"
        )

@router.get("/", response_model=PackListResponse)
async def list_packs(
    skip: int = Query(0, ge=0, description="Number of packs to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of packs to return"),
    creator_type: Optional[CreatorType] = Query(None, description="Filter by creator type"),
    pack_service: PackService = Depends(get_pack_service)
):
    """
    Get a list of trivia packs with optional filtering.
    
    Args:
        skip: Number of packs to skip for pagination
        limit: Maximum number of packs to return
        creator_type: Optional filter by creator type
        pack_service: Pack service dependency
        
    Returns:
        List of packs matching the criteria
    """
    try:
        logger.info(f"Retrieving packs with skip={skip}, limit={limit}, creator_type={creator_type}")
        
        # Get packs from repository
        packs = await pack_service.pack_repository.get_all()
        
        # Filter by creator_type if provided
        if creator_type:
            packs = [p for p in packs if p.creator_type == creator_type]
        
        # Apply pagination
        total = len(packs)
        paginated_packs = packs[skip:skip + limit]
        
        logger.info(f"Retrieved {total} packs, returning {len(paginated_packs)}")
        
        return PackListResponse(
            total=total,
            packs=paginated_packs
        )
        
    except Exception as e:
        # Log the error
        logger.error(f"Error retrieving packs: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve packs: {str(e)}"
        )

@router.get("/{pack_id}", response_model=PackResponse)
async def get_pack(
    pack_id: str,
    pack_service: PackService = Depends(get_pack_service)
):
    """
    Get a specific trivia pack by ID.
    
    Args:
        pack_id: ID of the pack to retrieve
        pack_service: Pack service dependency
        
    Returns:
        The requested pack
    """
    try:
        # Ensure pack_id is a valid UUID string
        pack_id = ensure_uuid(pack_id)
        
        logger.info(f"Retrieving pack with ID: {pack_id}")
        
        # Get the pack from repository
        pack = await pack_service.pack_repository.get_by_id(pack_id)
        
        if not pack:
            logger.warning(f"Pack with ID {pack_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pack with ID {pack_id} not found"
            )
        
        logger.info(f"Successfully retrieved pack: {pack.name}")
        return pack
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the error
        logger.error(f"Error retrieving pack with ID {pack_id}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve pack: {str(e)}"
        )