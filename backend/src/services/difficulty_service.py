# backend/src/services/difficulty_service.py
import uuid
from typing import List, Dict, Any, Optional

from ..models.pack_creation_data import PackCreationDataUpdate
from ..repositories.pack_creation_data_repository import PackCreationDataRepository
from ..utils.question_generation.pack_difficulty_creation import PackDifficultyCreation
from ..utils import ensure_uuid

class DifficultyService:
    """
    Service for managing difficulty descriptions for trivia packs.
    Handles storage, retrieval, and updates of difficulty-related data.
    """
    
    def __init__(self, pack_creation_data_repository: PackCreationDataRepository):
        """
        Initialize with required repositories.
        
        Args:
            pack_creation_data_repository: Repository for pack creation data operations
        """
        self.pack_creation_repository = pack_creation_data_repository
        # PackDifficultyCreation only expects llm_service, not pack_creation_data_repository
        self.difficulty_creator = PackDifficultyCreation()
    
    async def store_difficulty_descriptions(self, pack_id: uuid.UUID, difficulty_json: Dict[str, Dict[str, str]]) -> None:
        """
        Store difficulty descriptions in the pack_creation_data table.
        
        Args:
            pack_id: UUID of the pack
            difficulty_json: Nested dictionary of difficulty descriptions
        """
        # Ensure pack_id is a proper UUID object
        pack_id = ensure_uuid(pack_id)
        
        # Check if there's already data for this pack
        existing_data = await self.pack_creation_repository.get_by_pack_id(pack_id)
        
        if existing_data:
            # Update existing record with the dictionary directly
            update_data = PackCreationDataUpdate(
                custom_difficulty_description=difficulty_json
            )
            await self.pack_creation_repository.update(id=existing_data.id, obj_in=update_data)
        else:
            # For this scenario, we expect pack_creation_data to already exist
            # (created in the topic creation phase), but just in case:
            print(f"Warning: No existing pack creation data found for pack_id {pack_id}")
            # We would need additional information to create a new record
    
    async def get_existing_difficulty_descriptions(self, pack_id: uuid.UUID) -> Dict[str, Dict[str, str]]:
        """
        Retrieve existing difficulty descriptions for a pack.
        
        Args:
            pack_id: UUID of the pack
            
        Returns:
            Nested dictionary of difficulty descriptions
        """
        # Ensure pack_id is a proper UUID object
        pack_id = ensure_uuid(pack_id)
        
        creation_data = await self.pack_creation_repository.get_by_pack_id(pack_id)
        
        if creation_data and hasattr(creation_data, 'custom_difficulty_description'):
            # Get the stored data
            stored_data = creation_data.custom_difficulty_description
            
            # Check if we have valid dictionary data
            if isinstance(stored_data, dict) and stored_data:
                return stored_data
        
        # Return default structure if no data found or not in expected format
        return self.difficulty_creator._get_default_difficulty_structure()
    
    async def update_specific_difficulty_descriptions(
        self,
        pack_id: uuid.UUID,
        difficulty_updates: Dict[str, str]
    ) -> Dict[str, Dict[str, str]]:
        """
        Update specific difficulty descriptions without replacing all of them.
        
        Args:
            pack_id: UUID of the pack
            difficulty_updates: Dictionary mapping difficulty levels to their new custom descriptions
                               (e.g., {"Hard": "New hard description", "Expert": "New expert description"})
            
        Returns:
            Updated nested dictionary of difficulty descriptions
        """
        # Ensure pack_id is a proper UUID object
        pack_id = ensure_uuid(pack_id)
        
        # Get existing descriptions
        existing_descriptions = await self.get_existing_difficulty_descriptions(pack_id)
        
        # Update only the specified difficulty levels
        for level, new_custom_desc in difficulty_updates.items():
            if level in existing_descriptions:
                existing_descriptions[level]["custom"] = new_custom_desc
            else:
                # If level doesn't exist yet, create it with default base description
                base_desc = self.difficulty_creator.base_descriptions.get(level, "")
                existing_descriptions[level] = {
                    "base": base_desc,
                    "custom": new_custom_desc
                }
        
        # Store updated descriptions
        await self.store_difficulty_descriptions(pack_id, existing_descriptions)
        
        return existing_descriptions
    
    async def generate_and_store_difficulty_descriptions(
        self, 
        pack_id: uuid.UUID, 
        creation_name: str, 
        pack_topics: List[str]
    ) -> Dict[str, Dict[str, str]]:
        """
        Generate and store difficulty descriptions for a pack in JSON format.
        This will overwrite any existing difficulty descriptions.
        
        Args:
            pack_id: UUID of the pack
            creation_name: Name of the trivia pack
            pack_topics: List of topics in the pack
            
        Returns:
            Nested dictionary of difficulty descriptions
        """
        # Ensure pack_id is a proper UUID object
        pack_id = ensure_uuid(pack_id)
        
        # Generate custom descriptions using the utility
        custom_descriptions = await self.difficulty_creator.generate_difficulty_descriptions(
            creation_name=creation_name,
            pack_topics=pack_topics
        )
        
        # Convert to JSON structure
        difficulty_json = self.difficulty_creator.create_difficulty_json(custom_descriptions)
        
        # Store in database
        await self.store_difficulty_descriptions(
            pack_id=pack_id,
            difficulty_json=difficulty_json
        )
        
        return difficulty_json
    
    async def generate_and_handle_existing_difficulty_descriptions(
        self, 
        pack_id: uuid.UUID, 
        creation_name: str, 
        pack_topics: List[str],
        force_regenerate: bool = False
    ) -> Dict[str, Dict[str, str]]:
        """
        Handles the generation of difficulty descriptions while respecting existing ones.
        
        Args:
            pack_id: UUID of the pack
            creation_name: Name of the trivia pack
            pack_topics: List of topics in the pack
            force_regenerate: If True, will regenerate descriptions even if they exist
            
        Returns:
            Nested dictionary of difficulty descriptions
        """
        # Ensure pack_id is a proper UUID object
        pack_id = ensure_uuid(pack_id)
        
        # Check if difficulty descriptions already exist
        existing_descriptions = await self.get_existing_difficulty_descriptions(pack_id)
        
        # Check if we have any custom descriptions
        has_custom_descriptions = False
        for level_data in existing_descriptions.values():
            if level_data.get("custom", ""):
                has_custom_descriptions = True
                break
        
        # If descriptions exist and we don't want to regenerate, return them
        if has_custom_descriptions and not force_regenerate:
            return existing_descriptions
        
        # Otherwise, generate new descriptions
        return await self.generate_and_store_difficulty_descriptions(
            pack_id=pack_id,
            creation_name=creation_name,
            pack_topics=pack_topics
        )
    
    async def generate_specific_difficulty_descriptions(
        self,
        pack_id: uuid.UUID,
        creation_name: str,
        pack_topics: List[str],
        difficulty_levels: List[str]
    ) -> Dict[str, Dict[str, str]]:
        """
        Generate descriptions for specific difficulty levels and update them while preserving others.
        
        Args:
            pack_id: UUID of the pack
            creation_name: Name of the trivia pack
            pack_topics: List of topics in the pack
            difficulty_levels: List of difficulty levels to update (e.g., ["Hard", "Expert"])
            
        Returns:
            Updated nested dictionary of difficulty descriptions
        """
        # Ensure pack_id is a proper UUID object
        pack_id = ensure_uuid(pack_id)
        
        # Generate all difficulty descriptions (temporary)
        all_descriptions = await self.difficulty_creator.generate_difficulty_descriptions(
            creation_name=creation_name,
            pack_topics=pack_topics
        )
        
        # Extract only the requested difficulty levels
        updates = {level: all_descriptions.get(level, "") for level in difficulty_levels if level in all_descriptions}
        
        # Update only the specified levels
        return await self.update_specific_difficulty_descriptions(
            pack_id=pack_id,
            difficulty_updates=updates
        )