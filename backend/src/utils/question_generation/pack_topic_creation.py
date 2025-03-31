# backend/src/utils/question_generation/pack_topic_creation.py
import uuid
import logging
from typing import List, Optional
from ...models.pack_creation_data import PackCreationDataCreate, PackCreationDataUpdate
from ...repositories.pack_creation_data_repository import PackCreationDataRepository
from ..llm.llm_service import LLMService
from ..document_processing.processors import clean_text, normalize_text
from ..llm.llm_parsing_utils import parse_json_from_llm
from ...utils import ensure_uuid

# Setup logger
logger = logging.getLogger(__name__)

class PackTopicCreation:
    """
    Handles the creation and management of pack topics for trivia question generation.
    """
    
    def __init__(self, 
                 pack_creation_data_repository: PackCreationDataRepository, 
                 llm_service: Optional[LLMService] = None):
        """
        Initialize with required repositories and services.
        
        Args:
            pack_creation_data_repository: Repository for pack creation data operations
            llm_service: Service for LLM interactions. If None, creates a new instance.
        """
        self.pack_creation_repository = pack_creation_data_repository
        self.llm_service = llm_service or LLMService()
        
    async def create_pack_topics(self, creation_name: str, 
                               num_topics: int = 5) -> List[str]:
        """
        Create a list of topics for a trivia pack using LLM.
        
        Args:
            creation_name: The name of the trivia pack
            num_topics: Number of topics to generate
            
        Returns:
            List of generated topics
        """
        # Clean and normalize inputs using document_processing utilities
        creation_name = normalize_text(creation_name, lowercase=False)
        
        # Generate the prompt for topic creation
        prompt = self._build_topic_generation_prompt(
            creation_name=creation_name,
            num_topics=num_topics
        )
        
        # Generate topics using LLM - single call
        raw_response = await self.llm_service.generate_content(prompt)
        
        # Parse the raw response directly into JSON
        default_topics = []  # Default in case parsing fails
        topics_data = parse_json_from_llm(raw_response, default_topics)
        
        # Validate the result is a list of strings
        if isinstance(topics_data, list):
            # Convert any non-string items to strings
            topics = [str(item) for item in topics_data if item]
        else:
            topics = default_topics
        
        # Ensure we have the requested number of topics (truncate if we have too many)
        if len(topics) > num_topics:
            topics = topics[:num_topics]
            
        # Check if we got fewer topics than requested and output a warning
        if len(topics) < num_topics:
            logger.warning(
                f"Requested {num_topics} topics for '{creation_name}', but only received {len(topics)}. "
                f"Continuing with the available topics."
            )
            print(f"Warning: Requested {num_topics} topics but only got {len(topics)}")
        
        return topics
    
    def _build_topic_generation_prompt(self, creation_name: str, 
                                      num_topics: int = 5) -> str:
        """
        Build the prompt for topic creation.
        
        Args:
            creation_name: Name of the trivia pack
            num_topics: Number of topics to generate
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""Generate {num_topics} specific topics for a trivia pack named "{creation_name}".

The topics should:
- Be specific enough to generate interesting trivia questions
- Cover different aspects related to {creation_name}

IMPORTANT: Return the topics as a valid JSON array of strings in this exact format:
[
  "Topic 1",
  "Topic 2",
  "Topic 3"
]

For example, if the pack name was "World Geography", the response should be:
[
  "Mountain ranges across continents",
  "Island nations and archipelagos",
  "Capital cities of the world",
  "Major rivers and watersheds",
  "Desert ecosystems"
]

DO NOT include any additional text, explanations, or markdown - ONLY return the JSON array.
"""
        return prompt
    
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
        
        # Build prompt for additional topics
        additional_prompt = f"""Generate {num_additional_topics} new specific topics for a trivia pack named "{creation_name}".
        
Please provide topics DIFFERENT from these existing topics:
{', '.join(existing_topics)}

The topics should:
- Be specific enough to generate interesting trivia questions
- Cover different aspects related to {creation_name}

IMPORTANT: Return the topics as a valid JSON array of strings in this exact format:
[
  "New Topic 1",
  "New Topic 2",
  "New Topic 3"
]

DO NOT include any additional text, explanations, or markdown - ONLY return the JSON array.
"""
        
        # Generate additional topics - single call
        raw_response = await self.llm_service.generate_content(additional_prompt)
        
        # Parse the raw response directly into JSON
        default_topics = []
        new_topics_data = parse_json_from_llm(raw_response, default_topics)
        
        # Validate the result is a list of strings
        if isinstance(new_topics_data, list):
            new_topics = [str(item) for item in new_topics_data if item]
        else:
            new_topics = default_topics
            
        # Check if we got fewer topics than requested and output a warning
        if len(new_topics) < num_additional_topics:
            logger.warning(
                f"Requested {num_additional_topics} additional topics for '{creation_name}', "
                f"but only received {len(new_topics)}. Continuing with available topics."
            )
            print(f"Warning: Requested {num_additional_topics} additional topics but only got {len(new_topics)}")
        
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