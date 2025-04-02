# backend/src/api/routes/difficulty.py
from fastapi import APIRouter, Depends, HTTPException, Path, Body
import logging
# --- MODIFIED LINE: Added Optional ---
from typing import Dict, Optional # Import Optional for type hint

# --- UPDATED IMPORTS ---
from ..dependencies import get_difficulty_service, get_pack_service # Removed get_topic_service as it's indirectly used by DifficultyService now
from ..schemas import (
    DifficultyGenerateRequest, DifficultyUpdateRequest, DifficultyResponse,
    DifficultyDescription # Import DifficultyDescription for response construction if needed
)
from ...services.difficulty_service import DifficultyService
from ...services.pack_service import PackService # Keep PackService for validation
# --- END UPDATED IMPORTS ---
from ...utils import ensure_uuid

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=DifficultyResponse)
async def generate_difficulties(
    pack_id: str = Path(..., description="ID of the pack"),
    # Use Optional[Body(None)] to handle cases where the request body is empty or omitted
    # --- THIS LINE CAUSED THE ERROR - FIX IS THE IMPORT ABOVE ---
    difficulty_request: Optional[DifficultyGenerateRequest] = Body(None),
    difficulty_service: DifficultyService = Depends(get_difficulty_service),
    pack_service: PackService = Depends(get_pack_service)
):
    """
    Generate difficulty descriptions for a pack. Fetches pack name internally.
    """
    pack_id = ensure_uuid(pack_id)

    # Set defaults if not provided or request body is missing
    force_regenerate = difficulty_request.force_regenerate if difficulty_request else False

    # Verify the pack exists first (no need to extract creation_name here)
    try:
        pack = await pack_service.pack_repository.get_by_id(pack_id)
        if not pack:
            raise HTTPException(status_code=404, detail=f"Pack with ID {pack_id} not found")
    except Exception as e:
        logger.error(f"Error verifying pack existence: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Pack with ID {pack_id} not found")

    try:
        # Call the service method - it no longer needs creation_name or pack_topics
        difficulty_dict: Dict[str, DifficultyDescription] = await difficulty_service.generate_and_handle_existing_difficulty_descriptions(
            pack_id=pack_id,
            force_regenerate=force_regenerate
        )

        return DifficultyResponse(descriptions=difficulty_dict) # Ensure the response matches the schema

    except Exception as e:
        logger.error(f"Error generating difficulty descriptions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating difficulty descriptions: {str(e)}"
        )

@router.get("/", response_model=DifficultyResponse)
async def get_difficulties(
    pack_id: str = Path(..., description="ID of the pack"),
    difficulty_service: DifficultyService = Depends(get_difficulty_service),
    pack_service: PackService = Depends(get_pack_service) # Keep for validation
):
    """
    Get existing difficulty descriptions for a pack.
    """
    pack_id = ensure_uuid(pack_id)

    # Verify the pack exists
    try:
        pack = await pack_service.pack_repository.get_by_id(pack_id)
        if not pack:
            raise HTTPException(status_code=404, detail=f"Pack with ID {pack_id} not found")
    except Exception as e:
        logger.error(f"Error verifying pack existence: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Pack with ID {pack_id} not found")

    try:
        # Get existing difficulty descriptions directly from the service
        difficulties = await difficulty_service.get_existing_difficulty_descriptions(pack_id)

        return DifficultyResponse(descriptions=difficulties)

    except Exception as e:
        logger.error(f"Error retrieving difficulty descriptions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving difficulty descriptions: {str(e)}"
        )

@router.patch("/", response_model=DifficultyResponse)
async def update_difficulties(
    pack_id: str = Path(..., description="ID of the pack"),
    difficulty_request: DifficultyUpdateRequest = Body(...), # Request body is required
    difficulty_service: DifficultyService = Depends(get_difficulty_service),
    pack_service: PackService = Depends(get_pack_service) # Keep for validation
):
    """
    Update specific difficulty descriptions. Fetches pack name internally if needed by service.
    """
    pack_id = ensure_uuid(pack_id)

    # Verify the pack exists
    try:
        pack = await pack_service.pack_repository.get_by_id(pack_id)
        if not pack:
            raise HTTPException(status_code=404, detail=f"Pack with ID {pack_id} not found")
    except Exception as e:
        logger.error(f"Error verifying pack existence: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Pack with ID {pack_id} not found")

    try:
        # Call service to update specific descriptions (no longer needs creation_name)
        updated_difficulties = await difficulty_service.update_specific_difficulty_descriptions(
            pack_id=pack_id,
            difficulty_updates=difficulty_request.custom_descriptions
        )

        return DifficultyResponse(descriptions=updated_difficulties)

    except Exception as e:
        logger.error(f"Error updating difficulty descriptions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error updating difficulty descriptions: {str(e)}"
        )