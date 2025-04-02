# backend/src/api/routes/topic.py
from fastapi import APIRouter, Depends, HTTPException, Path, Body # Import Body
import logging
from typing import Optional # Import Optional

# --- UPDATED IMPORTS ---
from ..dependencies import get_topic_service, get_pack_service
from ..schemas import TopicGenerateRequest, TopicAddRequest, TopicResponse
from ...services.topic_service import TopicService
from ...services.pack_service import PackService
# --- END UPDATED IMPORTS ---
from ...utils import ensure_uuid

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=TopicResponse)
async def generate_topics(
    pack_id: str = Path(..., description="ID of the pack"),
    # Use Optional[Body(None)] to handle cases where the request body is empty or omitted
    topic_request: Optional[TopicGenerateRequest] = Body(None),
    topic_service: TopicService = Depends(get_topic_service),
    pack_service: PackService = Depends(get_pack_service)
):
    """
    Generate topics for a pack. Fetches pack name internally.
    """
    pack_id = ensure_uuid(pack_id)

    # Set defaults if request body is missing
    num_topics = topic_request.num_topics if topic_request else 5
    predefined_topic = topic_request.predefined_topic if topic_request else None

    # Verify pack exists to get its name for the service layer
    try:
        pack = await pack_service.pack_repository.get_by_id(pack_id)
        if not pack:
            raise HTTPException(status_code=404, detail=f"Pack with ID {pack_id} not found")
        pack_name = pack.name # Get pack name for service
    except Exception as e:
        logger.error(f"Error verifying pack existence: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Pack with ID {pack_id} not found")

    try:
        # Call service method - requires pack_name from the fetched pack
        topics = await topic_service.generate_or_use_topics(
            pack_id=pack_id,
            pack_name=pack_name, # <<< CHANGED: Pass pack_name instead of creation_name
            num_topics=num_topics,
            predefined_topic=predefined_topic
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
    topic_service: TopicService = Depends(get_topic_service),
    pack_service: PackService = Depends(get_pack_service) # Keep for validation
):
    """
    Get existing topics for a pack.
    """
    pack_id = ensure_uuid(pack_id)

    # Verify pack exists (optional, but good practice)
    try:
        pack = await pack_service.pack_repository.get_by_id(pack_id)
        if not pack:
            raise HTTPException(status_code=404, detail=f"Pack with ID {pack_id} not found")
    except Exception as e:
        logger.error(f"Error verifying pack existence: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Pack with ID {pack_id} not found")

    try:
        topics = await topic_service.get_existing_pack_topics(pack_id)
        return TopicResponse(topics=topics) # Returns empty list if none found

    except Exception as e:
        logger.error(f"Error retrieving topics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving topics: {str(e)}"
        )

@router.post("/additional", response_model=TopicResponse)
async def add_topics(
    pack_id: str = Path(..., description="ID of the pack"),
    # Use Optional[Body(None)] to handle cases where the request body is empty or omitted
    topic_request: Optional[TopicAddRequest] = Body(None),
    topic_service: TopicService = Depends(get_topic_service),
    pack_service: PackService = Depends(get_pack_service)
):
    """
    Add additional topics to a pack. Fetches pack name internally.
    """
    pack_id = ensure_uuid(pack_id)

    # Set defaults if request body is missing
    num_additional_topics = topic_request.num_additional_topics if topic_request else 3
    predefined_topic = topic_request.predefined_topic if topic_request else None

    # Verify pack exists to get its name for the service layer
    try:
        pack = await pack_service.pack_repository.get_by_id(pack_id)
        if not pack:
            raise HTTPException(status_code=404, detail=f"Pack with ID {pack_id} not found")
        pack_name = pack.name # Get pack name for service
    except Exception as e:
        logger.error(f"Error verifying pack existence: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Pack with ID {pack_id} not found")

    try:
        # Call service method - requires pack_name
        all_topics = await topic_service.add_additional_topics(
            pack_id=pack_id,
            pack_name=pack_name, # <<< CHANGED: Pass pack_name instead of creation_name
            num_additional_topics=num_additional_topics,
            predefined_topic=predefined_topic
        )

        return TopicResponse(topics=all_topics)

    except Exception as e:
        logger.error(f"Error adding topics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error adding topics: {str(e)}"
        )