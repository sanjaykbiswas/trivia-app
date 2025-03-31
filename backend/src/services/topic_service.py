# backend/src/services/topic_service.py
import uuid
import logging
from typing import List, Optional

from ..models.pack_creation_data import PackCreationDataCreate, PackCreationDataUpdate
from ..repositories.pack_creation_data_repository import PackCreationDataRepository
from ..utils.question_generation.pack_topic_creation import PackTopicCreation
from ..utils import ensure_uuid

# Setup logger
logger = logging.getLogger(__name__)

class TopicService:
    """
    Service for managing pack topics.
    Handles storage, retrieval, and addition of topics for trivia packs.
    """
    
    def __init__(self, pack_creation_data_repository: PackCreationDataRepository):
        """
        Initialize with required repositories.
        
        Args:
            pack_creation_data_repository: Repository for pack creation data operations
        """
        self.pack_creation_repository = pack_creation_data_repository
        self.topic_creator = PackTopicCreation(pack_creation_data_repository=None)
    
    async def store_pack_topics(self, pack_id: uuid.UUID, topics: List[str], 
                              creation_name: str) -> None:
        """
        Store topics in the pack_creation_data table.
        
        Args:
            pack_id: UUID of the pack
            topics: List of topics to store
            creation_name: Name of the pack/creator
        """
        # Ensure pack_id is a proper UUID object
        pack_id = ensure_uuid(pack_id)
        
        # Check if there's already data for this pack
        existing_data = await self.pack_creation_repository.get_by_pack_id(pack_id)
        
        if existing_data:
            # Update existing record
            update_data = PackCreationDataUpdate(
                pack_topics=topics
            )
            await self.pack_creation_repository.update(id=existing_data.id, obj_in=update_data)
        else:
            # Create new record
            new_data = PackCreationDataCreate(
                pack_id=pack_id,
                pack_topics=topics,
                creation_name=creation_name,  # Required field
                custom_difficulty_description={}  # Empty dictionary for now
            )
            await self.pack_creation_repository.create(obj_in=new_data)
    
    async def get_existing_pack_topics(self, pack_id: uuid.UUID) -> List[str]:
        """
        Retrieve existing topics for a pack.
        
        Args:
            pack_id: UUID of the pack
            
        Returns:
            List of existing topics
        """
        # Ensure pack_id is a proper UUID object
        pack_id = ensure_uuid(pack_id)
        
        creation_data = await self.pack_creation_repository.get_by_pack_id(pack_id)
        
        if creation_data and hasattr(creation_data, 'pack_topics'):
            return creation_data.pack_topics
        else:
            return []
    
    async def add_additional_topics(self, pack_id: uuid.UUID, 
                                  creation_name: str,
                                  num_additional_topics: int = 3) -> List[str]:
        """
        Add additional topics to an existing pack.
        
        Args:
            pack_id: UUID of the pack
            creation_name: The name of the trivia pack
            num_additional_topics: Number of new topics to add
            
        Returns:
            Full list of topics (existing + new)
        """
        # Ensure pack_id is a proper UUID object
        pack_id = ensure_uuid(pack_id)
        
        # Get existing topics
        existing_topics = await self.get_existing_pack_topics(pack_id)
        
        # Use the utility to create new topics based on existing ones
        new_topics = await self.topic_creator.create_additional_topics(
            existing_topics=existing_topics,
            creation_name=creation_name, 
            num_additional_topics=num_additional_topics
        )
        
        # Combine with existing, avoiding duplicates
        all_topics = existing_topics.copy()
        for topic in new_topics:
            if topic not in all_topics:
                all_topics.append(topic)
        
        # Store the updated list
        await self.store_pack_topics(
            pack_id=pack_id,
            topics=all_topics,
            creation_name=creation_name
        )
        
        return all_topics