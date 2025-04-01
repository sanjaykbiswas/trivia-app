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