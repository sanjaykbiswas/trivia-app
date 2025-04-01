# backend/src/services/difficulty_service.py
from typing import List, Dict, Any, Optional

from ..models.pack_creation_data import PackCreationDataCreate, PackCreationDataUpdate # Import Create schema
from ..repositories.pack_creation_data_repository import PackCreationDataRepository
from ..services.topic_service import TopicService # Import TopicService
from ..utils.question_generation.pack_difficulty_creation import PackDifficultyCreation
from ..utils import ensure_uuid
import logging # Import logging

# Configure logger
logger = logging.getLogger(__name__)

class DifficultyService:
    """
    Service for managing difficulty descriptions for trivia packs.
    Handles storage, retrieval, and updates of difficulty-related data.
    Uses TopicService to get pack topics.
    """

    def __init__(
        self,
        topic_service: TopicService, # Inject TopicService
        pack_creation_data_repository: PackCreationDataRepository # Keep PackCreationDataRepository
        ):
        """
        Initialize with required services and repositories.

        Args:
            topic_service: Service for topic-related operations.
            pack_creation_data_repository: Repository for pack creation data operations.
        """
        self.topic_service = topic_service
        self.pack_creation_repository = pack_creation_data_repository
        self.difficulty_creator = PackDifficultyCreation()

    async def store_difficulty_descriptions(self, pack_id: str, creation_name: str, difficulty_json: Dict[str, Dict[str, str]]) -> None:
        """
        Store difficulty descriptions in the pack_creation_data table.
        Creates the record if it doesn't exist.

        Args:
            pack_id: ID of the pack.
            creation_name: Name of the pack (used if creating the record).
            difficulty_json: Nested dictionary of difficulty descriptions.
        """
        pack_id_uuid = ensure_uuid(pack_id)
        existing_data = await self.pack_creation_repository.get_by_pack_id(pack_id_uuid)

        if existing_data:
            # Update existing record
            update_data = PackCreationDataUpdate(
                custom_difficulty_description=difficulty_json
            )
            await self.pack_creation_repository.update(id=existing_data.id, obj_in=update_data)
            logger.info(f"Updated difficulty descriptions for pack {pack_id_uuid}")
        else:
            # Create new record if it doesn't exist
            # This might happen if topics were somehow added without creating this record initially
            logger.warning(f"PackCreationData record not found for pack {pack_id_uuid}. Creating one.")
            create_data = PackCreationDataCreate(
                pack_id=pack_id_uuid,
                creation_name=creation_name, # Need creation_name here
                custom_difficulty_description=difficulty_json,
                # Add other defaults as needed by the Create schema
                seed_questions={}
            )
            await self.pack_creation_repository.create(obj_in=create_data)
            logger.info(f"Created PackCreationData and stored difficulty descriptions for pack {pack_id_uuid}")


    async def get_existing_difficulty_descriptions(self, pack_id: str) -> Dict[str, Dict[str, str]]:
        """
        Retrieve existing difficulty descriptions for a pack.

        Args:
            pack_id: ID of the pack.

        Returns:
            Nested dictionary of difficulty descriptions.
        """
        pack_id_uuid = ensure_uuid(pack_id)
        creation_data = await self.pack_creation_repository.get_by_pack_id(pack_id_uuid)

        if creation_data and hasattr(creation_data, 'custom_difficulty_description'):
            stored_data = creation_data.custom_difficulty_description
            if isinstance(stored_data, dict) and stored_data:
                # Ensure all expected levels exist, using defaults if needed
                default_structure = self.difficulty_creator._get_default_difficulty_structure()
                for level, default_content in default_structure.items():
                    if level not in stored_data:
                         stored_data[level] = default_content
                    elif "base" not in stored_data[level]: # Ensure base exists
                         stored_data[level]["base"] = default_content["base"]
                    # Custom can be missing or empty
                return stored_data

        logger.debug(f"No existing difficulty descriptions found for pack {pack_id_uuid}, returning default structure.")
        return self.difficulty_creator._get_default_difficulty_structure()

    async def update_specific_difficulty_descriptions(
        self,
        pack_id: str,
        creation_name: str, # Added creation_name for potential creation
        difficulty_updates: Dict[str, str]
    ) -> Dict[str, Dict[str, str]]:
        """
        Update specific difficulty descriptions without replacing all of them.

        Args:
            pack_id: ID of the pack.
            creation_name: Name of the pack (needed if creating PackCreationData).
            difficulty_updates: Dictionary mapping difficulty levels to their new custom descriptions.

        Returns:
            Updated nested dictionary of difficulty descriptions.
        """
        pack_id_uuid = ensure_uuid(pack_id)
        existing_descriptions = await self.get_existing_difficulty_descriptions(pack_id_uuid)

        for level, new_custom_desc in difficulty_updates.items():
            if level in existing_descriptions:
                existing_descriptions[level]["custom"] = new_custom_desc
            else:
                # If level doesn't exist yet (e.g., 'Mixed'), create it
                base_desc = self.difficulty_creator.base_descriptions.get(level, "")
                existing_descriptions[level] = {
                    "base": base_desc,
                    "custom": new_custom_desc
                }

        # Store updated descriptions
        await self.store_difficulty_descriptions(pack_id_uuid, creation_name, existing_descriptions)
        return existing_descriptions

    async def generate_and_store_difficulty_descriptions(
        self,
        pack_id: str,
        creation_name: str,
        pack_topics: List[str] # Now passed explicitly
    ) -> Dict[str, Dict[str, str]]:
        """
        Generate and store difficulty descriptions for a pack in JSON format.
        This will overwrite any existing difficulty descriptions.

        Args:
            pack_id: ID of the pack.
            creation_name: Name of the trivia pack.
            pack_topics: List of topics in the pack.

        Returns:
            Nested dictionary of difficulty descriptions.
        """
        pack_id_uuid = ensure_uuid(pack_id)

        if not pack_topics:
            logger.warning(f"Cannot generate difficulty descriptions for pack {pack_id_uuid} as it has no topics.")
            # Return default structure and attempt to store it
            difficulty_json = self.difficulty_creator._get_default_difficulty_structure()
        else:
            # Generate custom descriptions using the utility
            custom_descriptions = await self.difficulty_creator.generate_difficulty_descriptions(
                creation_name=creation_name,
                pack_topics=pack_topics
            )
            # Convert to JSON structure
            difficulty_json = self.difficulty_creator.create_difficulty_json(custom_descriptions)

        # Store in database
        await self.store_difficulty_descriptions(
            pack_id=pack_id_uuid,
            creation_name=creation_name,
            difficulty_json=difficulty_json
        )
        return difficulty_json

    async def generate_and_handle_existing_difficulty_descriptions(
        self,
        pack_id: str,
        creation_name: str,
        force_regenerate: bool = False
    ) -> Dict[str, Dict[str, str]]:
        """
        Handles the generation of difficulty descriptions while respecting existing ones.
        Fetches topics using TopicService.

        Args:
            pack_id: ID of the pack.
            creation_name: Name of the trivia pack.
            force_regenerate: If True, will regenerate descriptions even if they exist.

        Returns:
            Nested dictionary of difficulty descriptions.
        """
        pack_id_uuid = ensure_uuid(pack_id)
        existing_descriptions = await self.get_existing_difficulty_descriptions(pack_id_uuid)

        # Check if custom descriptions already exist and regeneration isn't forced
        has_custom_descriptions = any(d.get("custom", "") for d in existing_descriptions.values())
        if has_custom_descriptions and not force_regenerate:
            logger.info(f"Using existing difficulty descriptions for pack {pack_id_uuid}.")
            return existing_descriptions

        # Fetch topics needed for generation
        pack_topics = await self.topic_service.get_existing_pack_topics(pack_id_uuid)
        if not pack_topics:
             logger.warning(f"No topics found for pack {pack_id_uuid}. Cannot generate custom difficulty descriptions. Storing defaults.")
             # Store default descriptions if no topics exist
             default_structure = self.difficulty_creator._get_default_difficulty_structure()
             await self.store_difficulty_descriptions(pack_id_uuid, creation_name, default_structure)
             return default_structure

        # Generate and store new descriptions
        logger.info(f"Generating new difficulty descriptions for pack {pack_id_uuid}.")
        return await self.generate_and_store_difficulty_descriptions(
            pack_id=pack_id_uuid,
            creation_name=creation_name,
            pack_topics=pack_topics
        )

    async def generate_specific_difficulty_descriptions(
        self,
        pack_id: str,
        creation_name: str,
        difficulty_levels: List[str]
    ) -> Dict[str, Dict[str, str]]:
        """
        Generate descriptions for specific difficulty levels and update them.

        Args:
            pack_id: ID of the pack.
            creation_name: Name of the trivia pack.
            difficulty_levels: List of difficulty levels to update (e.g., ["Hard", "Expert"]).

        Returns:
            Updated nested dictionary of difficulty descriptions.
        """
        pack_id_uuid = ensure_uuid(pack_id)

        # Fetch topics needed for generation
        pack_topics = await self.topic_service.get_existing_pack_topics(pack_id_uuid)
        if not pack_topics:
             logger.warning(f"No topics found for pack {pack_id_uuid}. Cannot generate specific difficulty descriptions.")
             # Return existing/default descriptions
             return await self.get_existing_difficulty_descriptions(pack_id_uuid)

        # Generate all difficulty descriptions temporarily
        all_descriptions = await self.difficulty_creator.generate_difficulty_descriptions(
            creation_name=creation_name,
            pack_topics=pack_topics
        )

        # Extract only the requested difficulty levels
        updates = {level: all_descriptions.get(level, "") for level in difficulty_levels if level in all_descriptions}

        # Update only the specified levels
        return await self.update_specific_difficulty_descriptions(
            pack_id=pack_id_uuid,
            creation_name=creation_name, # Pass creation_name
            difficulty_updates=updates
        )