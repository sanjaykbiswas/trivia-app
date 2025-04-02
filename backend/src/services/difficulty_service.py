# backend/src/services/difficulty_service.py
from typing import List, Dict, Any, Optional
import logging

# --- UPDATED IMPORTS ---
from ..models.pack import PackUpdate # Import PackUpdate
from ..repositories.pack_repository import PackRepository # Import PackRepository
# --- END UPDATED IMPORTS ---
from ..services.topic_service import TopicService
from ..utils.question_generation.pack_difficulty_creation import PackDifficultyCreation
from ..utils import ensure_uuid

# Configure logger
logger = logging.getLogger(__name__)

class DifficultyService:
    """
    Service for managing difficulty descriptions for trivia packs.
    Stores descriptions directly within the Pack model.
    Uses TopicService to get pack topics for generation context.
    """

    def __init__(
        self,
        topic_service: TopicService,
        pack_repository: PackRepository # <<< CHANGED: Use PackRepository
        ):
        """
        Initialize with required services and repositories.

        Args:
            topic_service: Service for topic-related operations.
            pack_repository: Repository for pack operations.
        """
        self.topic_service = topic_service
        self.pack_repository = pack_repository # <<< CHANGED: Store PackRepository
        self.difficulty_creator = PackDifficultyCreation()

    async def store_difficulty_descriptions(self, pack_id: str, difficulty_json: Dict[str, Dict[str, str]]) -> bool:
        """
        Store difficulty descriptions in the packs table.

        Args:
            pack_id: ID of the pack.
            difficulty_json: Nested dictionary of difficulty descriptions.

        Returns:
            True if successful, False otherwise.
        """
        pack_id_uuid = ensure_uuid(pack_id)
        try:
            # Check if the pack exists first
            existing_pack = await self.pack_repository.get_by_id(pack_id_uuid)
            if not existing_pack:
                logger.error(f"Cannot store difficulty descriptions: Pack with ID {pack_id_uuid} not found.")
                return False

            # Update the pack record with the new descriptions
            update_data = PackUpdate(
                custom_difficulty_description=difficulty_json
            )
            updated_pack = await self.pack_repository.update(id=pack_id_uuid, obj_in=update_data)

            if updated_pack:
                logger.info(f"Stored/Updated difficulty descriptions for pack {pack_id_uuid}")
                return True
            else:
                # This case might happen if the update fails for some reason
                logger.error(f"Failed to update pack {pack_id_uuid} with difficulty descriptions.")
                return False
        except Exception as e:
             logger.error(f"Error storing difficulty descriptions for pack {pack_id_uuid}: {e}", exc_info=True)
             return False


    async def get_existing_difficulty_descriptions(self, pack_id: str) -> Dict[str, Dict[str, str]]:
        """
        Retrieve existing difficulty descriptions for a pack from the packs table.

        Args:
            pack_id: ID of the pack.

        Returns:
            Nested dictionary of difficulty descriptions. Returns defaults if not found or empty.
        """
        pack_id_uuid = ensure_uuid(pack_id)
        pack = await self.pack_repository.get_by_id(pack_id_uuid)

        # Default structure if pack not found or has no descriptions
        default_structure = self.difficulty_creator._get_default_difficulty_structure()

        if pack and hasattr(pack, 'custom_difficulty_description'):
            stored_data = pack.custom_difficulty_description
            # Check if stored_data is a non-empty dictionary
            if isinstance(stored_data, dict) and stored_data:
                # Ensure all expected levels exist, using defaults if needed
                for level, default_content in default_structure.items():
                    if level not in stored_data:
                         stored_data[level] = default_content
                    elif not isinstance(stored_data[level], dict): # Ensure inner value is a dict
                         stored_data[level] = default_content
                    elif "base" not in stored_data[level]: # Ensure base key exists
                         stored_data[level]["base"] = default_content["base"]
                    # "custom" can be missing or empty, which is fine
                return stored_data

        # Return default if pack not found, description field is missing/None, or empty
        logger.debug(f"No valid existing difficulty descriptions found for pack {pack_id_uuid}, returning default structure.")
        return default_structure

    async def update_specific_difficulty_descriptions(
        self,
        pack_id: str,
        difficulty_updates: Dict[str, str]
    ) -> Dict[str, Dict[str, str]]:
        """
        Update specific difficulty descriptions without replacing all of them.

        Args:
            pack_id: ID of the pack.
            difficulty_updates: Dictionary mapping difficulty levels to their new custom descriptions.

        Returns:
            Updated nested dictionary of difficulty descriptions, or default if update failed.
        """
        pack_id_uuid = ensure_uuid(pack_id)
        existing_descriptions = await self.get_existing_difficulty_descriptions(pack_id_uuid) # Fetches defaults if needed

        for level, new_custom_desc in difficulty_updates.items():
            if level in existing_descriptions:
                # Ensure the inner structure is a dict before updating
                if not isinstance(existing_descriptions[level], dict):
                    base_desc = self.difficulty_creator.base_descriptions.get(level, "")
                    existing_descriptions[level] = {"base": base_desc}
                existing_descriptions[level]["custom"] = new_custom_desc
            else:
                # If level doesn't exist yet (e.g., 'Mixed'), create it
                base_desc = self.difficulty_creator.base_descriptions.get(level, "")
                existing_descriptions[level] = {
                    "base": base_desc,
                    "custom": new_custom_desc
                }

        # Store updated descriptions
        success = await self.store_difficulty_descriptions(pack_id_uuid, existing_descriptions)
        return existing_descriptions if success else self.difficulty_creator._get_default_difficulty_structure()

    async def generate_and_store_difficulty_descriptions(
        self,
        pack_id: str,
        # creation_name is removed, will get from pack object
        pack_topics: List[str] # Now passed explicitly
    ) -> Dict[str, Dict[str, str]]:
        """
        Generate and store difficulty descriptions for a pack in JSON format.
        This will overwrite any existing difficulty descriptions in the pack record.

        Args:
            pack_id: ID of the pack.
            pack_topics: List of topics in the pack.

        Returns:
            Nested dictionary of difficulty descriptions, or default if generation/storage failed.
        """
        pack_id_uuid = ensure_uuid(pack_id)
        pack = await self.pack_repository.get_by_id(pack_id_uuid)
        if not pack:
            logger.error(f"Cannot generate difficulty descriptions: Pack {pack_id_uuid} not found.")
            return self.difficulty_creator._get_default_difficulty_structure()

        if not pack_topics:
            logger.warning(f"Cannot generate custom difficulty descriptions for pack {pack_id_uuid} as it has no topics.")
            difficulty_json = self.difficulty_creator._get_default_difficulty_structure()
        else:
            # Generate custom descriptions using the utility and pack name
            custom_descriptions = await self.difficulty_creator.generate_difficulty_descriptions(
                pack_name=pack.name, # <<< CHANGED: Use pack_name
                pack_topics=pack_topics
            )
            # Convert to JSON structure
            difficulty_json = self.difficulty_creator.create_difficulty_json(custom_descriptions)

        # Store in database
        success = await self.store_difficulty_descriptions(
            pack_id=pack_id_uuid,
            difficulty_json=difficulty_json
        )
        return difficulty_json if success else self.difficulty_creator._get_default_difficulty_structure()

    async def generate_and_handle_existing_difficulty_descriptions(
        self,
        pack_id: str,
        # creation_name is removed
        force_regenerate: bool = False
    ) -> Dict[str, Dict[str, str]]:
        """
        Handles the generation of difficulty descriptions while respecting existing ones.
        Fetches topics using TopicService. Stores descriptions in the Pack object.

        Args:
            pack_id: ID of the pack.
            force_regenerate: If True, will regenerate descriptions even if they exist.

        Returns:
            Nested dictionary of difficulty descriptions.
        """
        pack_id_uuid = ensure_uuid(pack_id)
        pack = await self.pack_repository.get_by_id(pack_id_uuid)
        if not pack:
            logger.error(f"Cannot handle difficulty descriptions: Pack {pack_id_uuid} not found.")
            return self.difficulty_creator._get_default_difficulty_structure()

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
             default_structure = self.difficulty_creator._get_default_difficulty_structure()
             await self.store_difficulty_descriptions(pack_id_uuid, default_structure)
             return default_structure

        # Generate and store new descriptions
        logger.info(f"Generating new difficulty descriptions for pack {pack_id_uuid}.")
        return await self.generate_and_store_difficulty_descriptions(
            pack_id=pack_id_uuid,
            # creation_name is derived internally now
            pack_topics=pack_topics
        )

    async def generate_specific_difficulty_descriptions(
        self,
        pack_id: str,
        # creation_name is removed
        difficulty_levels: List[str]
    ) -> Dict[str, Dict[str, str]]:
        """
        Generate descriptions for specific difficulty levels and update them in the Pack.

        Args:
            pack_id: ID of the pack.
            difficulty_levels: List of difficulty levels to update (e.g., ["Hard", "Expert"]).

        Returns:
            Updated nested dictionary of difficulty descriptions.
        """
        pack_id_uuid = ensure_uuid(pack_id)
        pack = await self.pack_repository.get_by_id(pack_id_uuid)
        if not pack:
            logger.error(f"Cannot generate specific difficulty descriptions: Pack {pack_id_uuid} not found.")
            return self.difficulty_creator._get_default_difficulty_structure()

        # Fetch topics needed for generation
        pack_topics = await self.topic_service.get_existing_pack_topics(pack_id_uuid)
        if not pack_topics:
             logger.warning(f"No topics found for pack {pack_id_uuid}. Cannot generate specific difficulty descriptions.")
             return await self.get_existing_difficulty_descriptions(pack_id_uuid) # Return existing

        # Generate all difficulty descriptions temporarily using pack name
        all_descriptions = await self.difficulty_creator.generate_difficulty_descriptions(
            pack_name=pack.name, # <<< CHANGED: Use pack_name
            pack_topics=pack_topics
        )

        # Extract only the requested difficulty levels
        updates = {level: all_descriptions.get(level, "") for level in difficulty_levels if level in all_descriptions}

        # Update only the specified levels in the pack record
        return await self.update_specific_difficulty_descriptions(
            pack_id=pack_id_uuid,
            difficulty_updates=updates
        )