# backend/src/services/seed_question_service.py
import logging
from typing import Dict, Optional, List

# --- UPDATED IMPORTS ---
from ..models.pack import PackUpdate # Import PackUpdate
from ..repositories.pack_repository import PackRepository # Import PackRepository
# --- END UPDATED IMPORTS ---
from ..repositories.topic_repository import TopicRepository
from ..utils.question_generation.seed_question_processor import SeedQuestionProcessor
from ..utils.question_generation.custom_instructions_creator import CustomInstructionsCreator
from ..utils import ensure_uuid

# Configure logger
logger = logging.getLogger(__name__)

class SeedQuestionService:
    """
    Service for managing seed questions (now stored in Pack) and
    topic-specific custom instructions (stored in Topic).
    """

    def __init__(
        self,
        pack_repository: PackRepository, # <<< CHANGED: Use PackRepository
        topic_repository: TopicRepository
        ):
        """
        Initialize with required repositories.

        Args:
            pack_repository: Repository for pack operations.
            topic_repository: Repository for topic operations.
        """
        self.pack_repository = pack_repository # <<< CHANGED: Store PackRepository
        self.topic_repository = topic_repository
        self.seed_processor = SeedQuestionProcessor(llm_service=None) # Assuming LLM not needed here
        self.custom_instructions_creator = CustomInstructionsCreator()

    # --- Seed Question Methods (Now use PackRepository) ---
    async def store_seed_questions(self, pack_id: str, seed_questions: Dict[str, str]) -> bool:
        """
        Store seed questions in the packs table.

        Args:
            pack_id: ID of the pack.
            seed_questions: Dictionary of question-answer pairs.

        Returns:
            Success flag.
        """
        try:
            pack_id_uuid = ensure_uuid(pack_id)
            existing_pack = await self.pack_repository.get_by_id(pack_id_uuid)

            if existing_pack:
                update_data = PackUpdate(seed_questions=seed_questions)
                updated_pack = await self.pack_repository.update(id=existing_pack.id, obj_in=update_data)
                if updated_pack:
                    logger.info(f"Stored seed questions for pack {pack_id_uuid}")
                    return True
                else:
                    logger.error(f"Failed to update pack {pack_id_uuid} with seed questions.")
                    return False
            else:
                logger.warning(f"Cannot store seed questions: Pack with ID {pack_id_uuid} not found.")
                return False
        except Exception as e:
            logger.error(f"Error storing seed questions for pack {pack_id_uuid}: {str(e)}")
            return False

    async def get_seed_questions(self, pack_id: str) -> Dict[str, str]:
        """
        Retrieve seed questions for a pack from the packs table.

        Args:
            pack_id: ID of the pack.

        Returns:
            Dictionary of seed questions. Returns empty dict if not found or empty.
        """
        pack_id_uuid = ensure_uuid(pack_id)
        pack = await self.pack_repository.get_by_id(pack_id_uuid)

        if pack and hasattr(pack, 'seed_questions') and isinstance(pack.seed_questions, dict):
            return pack.seed_questions
        return {}

    # --- Custom Instruction Methods (Remain largely unchanged, operate on TopicRepository) ---

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
        Uses seed questions from the Pack object.

        Args:
            pack_id: ID of the pack.
            pack_topic: Topic to base instructions on.

        Returns:
            Generated custom instructions or None if generation/storage failed.
        """
        pack_id_uuid = ensure_uuid(pack_id)
        try:
            # Get seed questions relevant to this topic if available (now from pack repo)
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