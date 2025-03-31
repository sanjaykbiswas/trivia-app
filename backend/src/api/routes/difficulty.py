# backend/src/api/routes/difficulty.py
from fastapi import APIRouter, Depends, HTTPException, Path, Body
import logging

from ..dependencies import get_difficulty_service, get_topic_service, get_pack_service
from ..schemas import DifficultyGenerateRequest, DifficultyUpdateRequest, DifficultyResponse
from ...services.difficulty_service import DifficultyService
from ...services.topic_service import TopicService
from ...services.pack_service import PackService
from ...utils import ensure_uuid

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=DifficultyResponse)
async def generate_difficulties(
    pack_id: str = Path(..., description="ID of the pack"),
    difficulty_request: DifficultyGenerateRequest = Body(None),
    difficulty_service: DifficultyService = Depends(get_difficulty_service),
    topic_service: TopicService = Depends(get_topic_service),
    pack_service: PackService = Depends(get_pack_service)
):
    """
    Generate difficulty descriptions for a pack.
    
    Args:
        pack_id: ID of the pack
        difficulty_request: Request data for difficulty generation
        difficulty_service: Difficulty service dependency
        topic_service: Topic service dependency
        
    Returns:
        Generated difficulty descriptions
    """
    # Ensure pack_id is a valid UUID string
    pack_id = ensure_uuid(pack_id)
    
    # Set defaults if not provided
    if difficulty_request is None:
        difficulty_request = DifficultyGenerateRequest()
    
    # First verify the pack exists
    try:
        pack_repo = pack_service.pack_repository
        pack = await pack_repo.get_by_id(pack_id)
        
        if not pack:
            raise HTTPException(
                status_code=404,
                detail=f"Pack with ID {pack_id} not found"
            )
            
        # Use the pack name if creation_name is not provided
        creation_name = difficulty_request.creation_name or pack.name
    except Exception as e:
        logger.error(f"Error verifying pack existence: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Pack with ID {pack_id} not found"
        )
    
    try:
        # Get existing topics (needed for difficulty generation)
        topics = await topic_service.get_existing_pack_topics(pack_id)
        
        if not topics:
            raise HTTPException(
                status_code=400,
                detail="Pack has no topics. Please generate topics first."
            )
        
        # Generate difficulties
        difficulty_json = await difficulty_service.generate_and_handle_existing_difficulty_descriptions(
            pack_id=pack_id,
            creation_name=creation_name,
            pack_topics=topics,
            force_regenerate=difficulty_request.force_regenerate
        )
        
        return DifficultyResponse(descriptions=difficulty_json)
    
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
    pack_service: PackService = Depends(get_pack_service)
):
    """
    Get existing difficulty descriptions for a pack.
    
    Args:
        pack_id: ID of the pack
        difficulty_service: Difficulty service dependency
        
    Returns:
        Existing difficulty descriptions
    """
    # Ensure pack_id is a valid UUID string
    pack_id = ensure_uuid(pack_id)
    
    # First verify the pack exists
    try:
        pack_repo = pack_service.pack_repository
        pack = await pack_repo.get_by_id(pack_id)
        
        if not pack:
            raise HTTPException(
                status_code=404,
                detail=f"Pack with ID {pack_id} not found"
            )
    except Exception as e:
        logger.error(f"Error verifying pack existence: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Pack with ID {pack_id} not found"
        )
    
    try:
        # Get existing difficulty descriptions
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
    difficulty_request: DifficultyUpdateRequest = Body(...),
    difficulty_service: DifficultyService = Depends(get_difficulty_service),
    topic_service: TopicService = Depends(get_topic_service),
    pack_service: PackService = Depends(get_pack_service)
):
    """
    Update specific difficulty descriptions.
    
    Args:
        pack_id: ID of the pack
        difficulty_request: Request data for updating difficulties
        difficulty_service: Difficulty service dependency
        topic_service: Topic service dependency
        
    Returns:
        Updated difficulty descriptions
    """
    # Ensure pack_id is a valid UUID string
    pack_id = ensure_uuid(pack_id)
    
    # First verify the pack exists
    try:
        pack_repo = pack_service.pack_repository
        pack = await pack_repo.get_by_id(pack_id)
        
        if not pack:
            raise HTTPException(
                status_code=404,
                detail=f"Pack with ID {pack_id} not found"
            )
            
        # Use the pack name if creation_name is not provided
        creation_name = difficulty_request.creation_name or pack.name
    except Exception as e:
        logger.error(f"Error verifying pack existence: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Pack with ID {pack_id} not found"
        )
    
    try:
        # Update specific difficulty descriptions
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