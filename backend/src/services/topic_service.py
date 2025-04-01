# backend/src/services/topic_service.py
import logging
from typing import List, Optional

# Removed PackCreationData imports as they are no longer directly used for topics
from ..repositories.topic_repository import TopicRepository # Changed import
from ..models.topic import TopicCreate # Import the create schema
from ..utils.question_generation.pack_topic_creation import PackTopicCreation
from ..utils.llm.llm_service import LLMService
from ..utils import ensure_uuid

# Setup logger
logger = logging.getLogger(__name__)

class TopicService:
    """
    Service for managing pack topics using the dedicated 'topics' table.
    Handles creation, retrieval, and addition of topics for trivia packs.
    """

    def __init__(self, topic_repository: TopicRepository): # Changed dependency
        """
        Initialize with required repositories.

        Args:
            topic_repository: Repository for topic operations.
        """
        self.topic_repository = topic_repository # Renamed attribute
        llm_service = LLMService()
        self.topic_creator = PackTopicCreation(llm_service=llm_service)

    async def store_pack_topics(self, pack_id: str, topics: List[str]) -> List[str]:
        """
        Store topics in the 'topics' table for a specific pack.
        It tries to create each topic and handles potential duplicates based on
        the repository's logic (or unique constraint).

        Args:
            pack_id: ID of the pack.
            topics: List of topic names to store.

        Returns:
            List of topic names that were successfully stored or already existed.
        """
        pack_id_uuid = ensure_uuid(pack_id)
        stored_topic_names = []

        for topic_name in topics:
            topic_create = TopicCreate(pack_id=pack_id_uuid, name=topic_name.strip())
            try:
                # Use the repository's create_topic method which handles checks/creation
                topic_obj = await self.topic_repository.create_topic(topic_create)
                if topic_obj:
                    stored_topic_names.append(topic_obj.name)
                else:
                    # This might happen if create_topic returns None on failure without raising
                    logger.warning(f"Failed to store topic '{topic_name}' for pack {pack_id_uuid}")
            except Exception as e:
                # Log error but continue trying to store other topics
                logger.error(f"Error storing topic '{topic_name}' for pack {pack_id_uuid}: {e}")

        return stored_topic_names

    async def get_existing_pack_topics(self, pack_id: str) -> List[str]:
        """
        Retrieve existing topic names for a pack from the 'topics' table.

        Args:
            pack_id: ID of the pack.

        Returns:
            List of existing topic names.
        """
        pack_id_uuid = ensure_uuid(pack_id)
        try:
            topic_objects = await self.topic_repository.get_by_pack_id(pack_id_uuid)
            return [topic.name for topic in topic_objects]
        except Exception as e:
            logger.error(f"Error retrieving topics for pack {pack_id_uuid}: {e}")
            return []

    async def generate_or_use_topics(self, pack_id: str,
                                 creation_name: str,
                                 num_topics: int = 5,
                                 predefined_topic: Optional[str] = None) -> List[str]:
        """
        Generate topics or use a predefined topic, storing them in the 'topics' table.

        Args:
            pack_id: ID of the pack.
            creation_name: The name of the trivia pack (used for generation context).
            num_topics: Number of topics to generate (if no predefined topic).
            predefined_topic: Optional predefined topic to use instead of generation.

        Returns:
            List of topics (either generated or just the predefined one) successfully stored.
        """
        pack_id_uuid = ensure_uuid(pack_id)
        topic_names_to_store = []

        if predefined_topic:
            topic_names_to_store = [predefined_topic.strip()]
            logger.info(f"Using predefined topic for pack {pack_id_uuid}: {predefined_topic}")
        else:
            logger.info(f"Generating {num_topics} topics for pack {pack_id_uuid} ('{creation_name}')")
            # Generate topic names using LLM
            topic_names_to_store = await self.topic_creator.create_pack_topics(
                creation_name=creation_name,
                num_topics=num_topics
            )

        # Store the generated/predefined topic names
        if topic_names_to_store:
            stored_topics = await self.store_pack_topics(pack_id_uuid, topic_names_to_store)
            return stored_topics
        else:
            logger.warning(f"No topics to store for pack {pack_id_uuid}.")
            return []

    async def add_additional_topics(self, pack_id: str,
                                  creation_name: str,
                                  num_additional_topics: int = 3,
                                  predefined_topic: Optional[str] = None) -> List[str]:
        """
        Add additional topics to an existing pack, storing them in the 'topics' table.

        Args:
            pack_id: ID of the pack.
            creation_name: The name of the trivia pack (used for generation context).
            num_additional_topics: Number of new topics to generate/add.
            predefined_topic: Optional predefined topic to add directly.

        Returns:
            Full list of topic names for the pack after additions.
        """
        pack_id_uuid = ensure_uuid(pack_id)

        # Get existing topic names first
        existing_topic_names = await self.get_existing_pack_topics(pack_id_uuid)
        new_topic_names_to_store = []

        if predefined_topic:
            cleaned_topic = predefined_topic.strip()
            if cleaned_topic not in existing_topic_names:
                new_topic_names_to_store.append(cleaned_topic)
                logger.info(f"Adding predefined additional topic: {cleaned_topic}")
            else:
                logger.warning(f"Predefined topic '{cleaned_topic}' already exists. Not adding.")
        else:
            # Generate additional topic names, avoiding existing ones
            logger.info(f"Generating {num_additional_topics} additional topics for pack {pack_id_uuid}")
            new_topic_names_to_store = await self.topic_creator.create_additional_topics(
                existing_topics=existing_topic_names,
                creation_name=creation_name,
                num_additional_topics=num_additional_topics
            )

        # Store the newly generated/added topic names
        if new_topic_names_to_store:
            await self.store_pack_topics(pack_id_uuid, new_topic_names_to_store)
        else:
            logger.info(f"No new topics generated or provided to add for pack {pack_id_uuid}.")

        # Return the full updated list of topic names for the pack
        return await self.get_existing_pack_topics(pack_id_uuid)