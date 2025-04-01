# backend/src/services/seed_question_service.py
import logging
from typing import Dict, Optional, List

from ..models.pack_creation_data import PackCreationDataUpdate
from ..repositories.pack_creation_data_repository import PackCreationDataRepository
from ..repositories.topic_repository import TopicRepository # Import TopicRepository
from ..utils.question_generation.seed_question_processor import SeedQuestionProcessor
from ..utils.question_generation.custom_instructions_creator import CustomInstructionsCreator
from ..utils import ensure_uuid

# Configure logger
logger = logging.getLogger(__name__)

class SeedQuestionService:
    """
    Service for managing seed questions and topic-specific custom instructions for trivia packs.
    """

    def __init__(
        self,
        pack_creation_data_repository: PackCreationDataRepository,
        topic_repository: TopicRepository # Inject TopicRepository
        ):
        """
        Initialize with required repositories.

        Args:
            pack_creation_data_repository: Repository for pack creation data operations.
            topic_repository: Repository for topic operations.
        """
        self.pack_creation_repository = pack_creation_data_repository
        self.topic_repository = topic_repository # Store TopicRepository
        self.seed_processor = SeedQuestionProcessor(llm_service=None)
        self.custom_instructions_creator = CustomInstructionsCreator()

    # --- Seed Question Methods (Unchanged) ---
    async def store_seed_questions(self, pack_id: str, seed_questions: Dict[str, str]) -> bool:
        """
        Store seed questions in the pack_creation_data table.

        Args:
            pack_id: ID of the pack.
            seed_questions: Dictionary of question-answer pairs.

        Returns:
            Success flag.
        """
        try:
            pack_id_uuid = ensure_uuid(pack_id)
            existing_data = await self.pack_creation_repository.get_by_pack_id(pack_id_uuid)

            if existing_data:
                update_data = PackCreationDataUpdate(seed_questions=seed_questions)
                await self.pack_creation_repository.update(id=existing_data.id, obj_in=update_data)
                logger.info(f"Stored seed questions for pack {pack_id_uuid}")
                return True
            else:
                logger.warning(f"No existing pack creation data found for pack_id {pack_id_uuid} to store seed questions.")
                return False
        except Exception as e:
            logger.error(f"Error storing seed questions for pack {pack_id_uuid}: {str(e)}")
            return False

    async def get_seed_questions(self, pack_id: str) -> Dict[str, str]:
        """
        Retrieve seed questions for a pack.

        Args:
            pack_id: ID of the pack.

        Returns:
            Dictionary of seed questions.
        """
        pack_id_uuid = ensure_uuid(pack_id)
        creation_data = await self.pack_creation_repository.get_by_pack_id(pack_id_uuid)

        if creation_data and hasattr(creation_data, 'seed_questions') and creation_data.seed_questions:
            return creation_data.seed_questions
        return {}

    # --- Custom Instruction Methods (Refactored for per-topic) ---

    async def store_topic_custom_instruction(self, pack_id: str, topic_name: str, custom_instruction: str) -> bool:
        """
        Store custom instructions for a specific topic in the 'topics' table.

        Args:
            pack_id: ID of the pack.
            topic_name: The name of the topic.
            custom_instruction: Custom instructions for the topic.

        Returns:
            Success flag.
        """
        pack_id_uuid = ensure_uuid(pack_id)
        try:
            # Find the topic record
            topic_record = await self.topic_repository.get_by_name_and_pack_id(topic_name, pack_id_uuid)

            if topic_record:
                # Update the instruction for the existing topic
                updated_topic = await self.topic_repository.update_custom_instruction(
                    topic_id=topic_record.id,
                    instruction=custom_instruction
                )
                if updated_topic:
                    logger.info(f"Stored custom instruction for topic '{topic_name}' in pack {pack_id_uuid}")
                    return True
                else:
                    logger.error(f"Failed to update custom instruction for topic '{topic_name}' in pack {pack_id_uuid}")
                    return False
            else:
                logger.warning(f"Topic '{topic_name}' not found in pack {pack_id_uuid}. Cannot store custom instruction.")
                return False
        except Exception as e:
            logger.error(f"Error storing custom instruction for topic '{topic_name}' in pack {pack_id_uuid}: {str(e)}")
            return False

    async def get_topic_custom_instruction(self, pack_id: str, topic_name: str) -> Optional[str]:
        """
        Retrieve custom instructions for a specific topic.

        Args:
            pack_id: ID of the pack.
            topic_name: The name of the topic.

        Returns:
            Custom instructions string or None if not found.
        """
        pack_id_uuid = ensure_uuid(pack_id)
        try:
            topic_record = await self.topic_repository.get_by_name_and_pack_id(topic_name, pack_id_uuid)
            if topic_record:
                return topic_record.custom_instruction
            else:
                logger.debug(f"No topic record found for '{topic_name}' in pack {pack_id_uuid}")
                return None
        except Exception as e:
            logger.error(f"Error retrieving custom instruction for topic '{topic_name}' in pack {pack_id_uuid}: {str(e)}")
            return None

    async def get_all_topic_instructions(self, pack_id: str) -> Dict[str, Optional[str]]:
        """
        Retrieve all custom instructions for all topics in a pack.

        Args:
            pack_id: ID of the pack.

        Returns:
            Dictionary mapping topic names to their custom instructions.
        """
        pack_id_uuid = ensure_uuid(pack_id)
        instructions_map = {}
        try:
            topics = await self.topic_repository.get_by_pack_id(pack_id_uuid)
            for topic in topics:
                instructions_map[topic.name] = topic.custom_instruction
            return instructions_map
        except Exception as e:
            logger.error(f"Error retrieving all topic instructions for pack {pack_id_uuid}: {e}")
            return {}

    async def generate_custom_instructions(self,
                                         pack_id: str,
                                         pack_topic: str) -> Optional[str]:
        """
        Generate and store custom instructions for a specific topic.

        Args:
            pack_id: ID of the pack.
            pack_topic: Topic to base instructions on.

        Returns:
            Generated custom instructions or None if generation/storage failed.
        """
        pack_id_uuid = ensure_uuid(pack_id)
        try:
            # Get seed questions relevant to this topic if available
            all_seed_questions = await self.get_seed_questions(pack_id_uuid)
            # Simple filtering: check if topic name is in the question text (case-insensitive)
            topic_seeds = {q: a for q, a in all_seed_questions.items() if pack_topic.lower() in q.lower()}

            # Generate custom instructions using the creator utility
            custom_instructions = await self.custom_instructions_creator.generate_custom_instructions(
                pack_topic=pack_topic,
                seed_questions=topic_seeds # Pass potentially filtered seeds
            )

            if not custom_instructions:
                 logger.warning(f"LLM failed to generate custom instructions for topic '{pack_topic}' in pack {pack_id_uuid}")
                 return None

            # Store the generated instructions for this specific topic
            success = await self.store_topic_custom_instruction(
                pack_id=pack_id_uuid,
                topic_name=pack_topic,
                custom_instruction=custom_instructions
            )

            if success:
                return custom_instructions
            else:
                logger.warning(f"Failed to store generated custom instructions for topic '{pack_topic}' in pack {pack_id_uuid}")
                return None # Return None even if generated, if storage failed

        except Exception as e:
            logger.error(f"Error generating or storing custom instructions for topic '{pack_topic}' in pack {pack_id_uuid}: {str(e)}")
            return None

    # Removed process_and_store_manual_instructions as it's ambiguous without a topic context.