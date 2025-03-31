# backend/src/api/routes/topic.py
from fastapi import APIRouter, Depends, HTTPException, Path
import logging

from ..dependencies import get_topic_service, get_pack_service
from ..schemas import TopicGenerateRequest, TopicAddRequest, TopicResponse
from ...services.topic_service import TopicService
from ...services.pack_service import PackService
from ...utils import ensure_uuid

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=TopicResponse)
async def generate_topics(
    pack_id: str = Path(..., description="ID of the pack"),
    topic_request: TopicGenerateRequest = None,
    topic_service: TopicService = Depends(get_topic_service),
    pack_service: PackService = Depends(get_pack_service)
):
    """
    Generate topics for a pack.
    
    Args:
        pack_id: ID of the pack
        topic_request: Request data for topic generation
        topic_service: Topic service dependency
        pack_service: Pack service dependency
        
    Returns:
        Generated topics
    """
    # Ensure pack_id is a valid UUID string
    pack_id = ensure_uuid(pack_id)
    
    # Set defaults if not provided
    if topic_request is None:
        topic_request = TopicGenerateRequest()
    
    # Check if the pack exists
    exists, pack_id_check = await pack_service.validate_creation_name("")
    if not pack_id_check:
        raise HTTPException(
            status_code=404,
            detail=f"Pack with ID {pack_id} not found"
        )
    
    # Get or set creation name
    creation_name = topic_request.creation_name
    if not creation_name:
        # In a real implementation, this would get the pack name from the repository
        # For now, using a placeholder
        creation_name = "Default Pack Name"
    
    try:
        # Generate topics
        topics = await topic_service.topic_creator.create_pack_topics(
            creation_name=creation_name,
            num_topics=topic_request.num_topics
        )
        
        # Store topics
        await topic_service.store_pack_topics(
            pack_id=pack_id,
            topics=topics,
            creation_name=creation_name
        )
        
        return TopicResponse(topics=topics)
    
    except Exception as e:
        logger.error(f"Error generating topics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating topics: {str(e)}"
        )

@router.get("/", response_model=TopicResponse)
async def get_topics(
    pack_id: str = Path(..., description="ID of the pack"),
    topic_service: TopicService = Depends(get_topic_service)
):
    """
    Get existing topics for a pack.
    
    Args:
        pack_id: ID of the pack
        topic_service: Topic service dependency
        
    Returns:
        Existing topics
    """
    # Ensure pack_id is a valid UUID string
    pack_id = ensure_uuid(pack_id)
    
    try:
        # Get existing topics
        topics = await topic_service.get_existing_pack_topics(pack_id)
        
        if not topics:
            return TopicResponse(topics=[])
        
        return TopicResponse(topics=topics)
    
    except Exception as e:
        logger.error(f"Error retrieving topics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving topics: {str(e)}"
        )

@router.post("/additional", response_model=TopicResponse)
async def add_topics(
    pack_id: str = Path(..., description="ID of the pack"),
    topic_request: TopicAddRequest = None,
    topic_service: TopicService = Depends(get_topic_service),
    pack_service: PackService = Depends(get_pack_service)
):
    """
    Add additional topics to a pack.
    
    Args:
        pack_id: ID of the pack
        topic_request: Request data for adding topics
        topic_service: Topic service dependency
        pack_service: Pack service dependency
        
    Returns:
        All topics including newly added ones
    """
    # Ensure pack_id is a valid UUID string
    pack_id = ensure_uuid(pack_id)
    
    # Set defaults if not provided
    if topic_request is None:
        topic_request = TopicAddRequest()
    
    # Get or set creation name
    creation_name = topic_request.creation_name
    if not creation_name:
        # In a real implementation, this would get the pack name from the repository
        # For now, using a placeholder
        creation_name = "Default Pack Name"
    
    try:
        # Add additional topics
        all_topics = await topic_service.add_additional_topics(
            pack_id=pack_id,
            creation_name=creation_name,
            num_additional_topics=topic_request.num_additional_topics
        )
        
        return TopicResponse(topics=all_topics)
    
    except Exception as e:
        logger.error(f"Error adding topics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error adding topics: {str(e)}"
        )