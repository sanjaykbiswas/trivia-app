# backend/src/utils/question_generation/pack_topic_creation.py
import uuid
from typing import List, Optional
from ...models.pack_creation_data import PackCreationDataCreate, PackCreationDataUpdate
from ...repositories.pack_creation_data_repository import PackCreationDataRepository
from ..llm.llm_service import LLMService
from ..document_processing.processors import clean_text, normalize_text
from ..llm.llm_parsing_utils import extract_bullet_list

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
                               creation_description: Optional[str] = None, 
                               num_topics: int = 5) -> List[str]:
        """
        Create a list of topics for a trivia pack using LLM.
        
        Args:
            creation_name: The name of the trivia pack
            creation_description: Optional description of the pack
            num_topics: Number of topics to generate
            
        Returns:
            List of generated topics
        """
        # Clean and normalize inputs using document_processing utilities
        creation_name = normalize_text(creation_name, lowercase=False)
        if creation_description:
            creation_description = clean_text(creation_description)
        
        # Generate the prompt for topic creation
        prompt = self._build_topic_generation_prompt(
            creation_name=creation_name,
            creation_description=creation_description,
            num_topics=num_topics
        )
        
        # Generate topics using LLM
        raw_response = await self.llm_service.generate_content(prompt)
        
        # Process the LLM response
        processed_response = await self.llm_service.process_llm_response(raw_response)
        
        # Parse the response into a clean list of topics using the new parsing utility
        topics = extract_bullet_list(processed_response)
        
        # Ensure we have the requested number of topics
        if len(topics) < num_topics:
            # If not enough topics, try again with more requested to compensate
            additional_needed = num_topics - len(topics)
            
            # Create a new prompt asking for additional topics
            additional_prompt = self._build_topic_generation_prompt(
                creation_name=creation_name,
                creation_description=creation_description,
                num_topics=additional_needed + 2  # Ask for a couple extra as buffer
            )
            
            raw_response = await self.llm_service.generate_content(additional_prompt)
            processed_response = await self.llm_service.process_llm_response(raw_response)
            
            # Parse additional topics and combine
            additional_topics = extract_bullet_list(processed_response)
            topics.extend(additional_topics)
            
            # Ensure we don't exceed the requested number
            topics = topics[:num_topics]
        
        return topics
    
    def _build_topic_generation_prompt(self, creation_name: str, 
                                      creation_description: Optional[str] = None,
                                      num_topics: int = 5) -> str:
        """
        Build the prompt for topic generation.
        
        Args:
            creation_name: Name of the trivia pack
            creation_description: Optional description
            num_topics: Number of topics to generate
            
        Returns:
            Formatted prompt string
        """
        description_text = f"\nDescription: {creation_description}" if creation_description else ""
        
        prompt = f"""Generate {num_topics} specific topics for a trivia pack named "{creation_name}".{description_text}

The topics should:
- Be specific enough to generate interesting trivia questions
- Cover different aspects related to {creation_name}
- Be presented as a simple bullet list (one topic per bullet)
- Not have any extra text, just the bullet list

For example, if the pack name was "World Geography":
- Mountain ranges across continents
- Island nations and archipelagos
- Capital cities of the world
- Major rivers and watersheds
- Desert ecosystems

Return ONLY the bullet list, with no additional text before or after.
"""
        return prompt
    
    async def store_pack_topics(self, pack_id: uuid.UUID, topics: List[str], 
                              creation_name: str,
                              creation_description: Optional[str] = None) -> None:
        """
        Store topics in the pack_creation_data table.
        
        Args:
            pack_id: UUID of the pack
            topics: List of topics to store
            creation_name: Name of the pack/creator
            creation_description: Optional description to store
        """
        # Check if there's already data for this pack
        existing_data = await self.pack_creation_repository.get_by_pack_id(pack_id)
        
        if existing_data:
            # Update existing record
            update_data = PackCreationDataUpdate(
                pack_topics=topics,
                creation_description=creation_description
            )
            await self.pack_creation_repository.update(id=existing_data.id, obj_in=update_data)
        else:
            # Create new record
            new_data = PackCreationDataCreate(
                pack_id=pack_id,
                pack_topics=topics,
                creation_name=creation_name,  # Required field
                creation_description=creation_description,
                custom_difficulty_description=[]  # Empty list for now
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
        creation_data = await self.pack_creation_repository.get_by_pack_id(pack_id)
        
        if creation_data and hasattr(creation_data, 'pack_topics'):
            return creation_data.pack_topics
        else:
            return []
    
    async def add_additional_topics(self, pack_id: uuid.UUID, 
                                  creation_name: str,
                                  creation_description: Optional[str] = None,
                                  num_additional_topics: int = 3) -> List[str]:
        """
        Add additional topics to an existing pack.
        
        Args:
            pack_id: UUID of the pack
            creation_name: The name of the trivia pack
            creation_description: Optional description of the pack
            num_additional_topics: Number of new topics to add
            
        Returns:
            Full list of topics (existing + new)
        """
        # Get existing topics
        existing_topics = await self.get_existing_pack_topics(pack_id)
        
        # Build prompt for additional topics
        additional_prompt = f"""Generate {num_additional_topics} new specific topics for a trivia pack named "{creation_name}".
        
{creation_description or ''}

Please provide topics DIFFERENT from these existing topics:
{', '.join(existing_topics)}

The topics should:
- Be specific enough to generate interesting trivia questions
- Cover different aspects related to {creation_name}
- Be presented as a simple bullet list (one topic per bullet)
- Not have any extra text, just the bullet list

Return ONLY the bullet list, with no additional text before or after.
"""
        
        # Generate additional topics
        raw_response = await self.llm_service.generate_content(additional_prompt)
        
        # Parse new topics using the new parsing utility
        new_topics = extract_bullet_list(raw_response)
        
        # Combine with existing, avoiding duplicates
        all_topics = existing_topics.copy()
        for topic in new_topics:
            if topic not in all_topics:
                all_topics.append(topic)
        
        # Store the updated list
        await self.store_pack_topics(
            pack_id=pack_id,
            topics=all_topics,
            creation_name=creation_name,  # Added required parameter
            creation_description=creation_description
        )
        
        return all_topics