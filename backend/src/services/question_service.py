# backend/src/services/question_service.py
import uuid
import logging
import json
import traceback
import asyncio # Import asyncio
from typing import List, Dict, Any, Optional, Union, Tuple

from ..models.question import Question, QuestionCreate, QuestionUpdate, DifficultyLevel
from ..repositories.question_repository import QuestionRepository
from ..repositories.pack_creation_data_repository import PackCreationDataRepository
from ..utils.question_generation.question_generator import QuestionGenerator
# We no longer need IncorrectAnswerGenerator or related imports here, as it's handled by IncorrectAnswerService
# from ..utils.question_generation.incorrect_answer_generator import IncorrectAnswerGenerator
# from ..models.incorrect_answers import IncorrectAnswersCreate
from ..api.schemas.question import TopicQuestionConfig # Import the new schema
from ..utils import ensure_uuid

# Configure logger
logger = logging.getLogger(__name__)

class QuestionService:
    """
    Service for question management operations.

    Handles business logic related to creating, retrieving,
    and managing trivia questions. Does NOT handle incorrect answer generation.
    """

    def __init__(
        self,
        question_repository: QuestionRepository,
        pack_creation_data_repository: Optional[PackCreationDataRepository] = None,
        question_generator: Optional[QuestionGenerator] = None,
        # Remove incorrect answer dependencies from this service
        # incorrect_answer_generator: Optional[IncorrectAnswerGenerator] = None,
        # incorrect_answers_repository: Optional[Any] = None # Using Any to avoid circular imports if needed
    ):
        """
        Initialize the service with required repositories.
        """
        self.question_repository = question_repository
        self.pack_creation_data_repository = pack_creation_data_repository
        self.question_generator = question_generator or QuestionGenerator()
        # self.incorrect_answer_generator = incorrect_answer_generator or IncorrectAnswerGenerator() # Removed
        # self.incorrect_answers_repository = incorrect_answers_repository # Removed
        self.debug_enabled = False

    async def _create_question(self, question_data: Dict[str, Any]) -> Optional[Question]:
        """
        Helper method to create a single question in the database.
        Validates data and uses the repository.
        """
        try:
            if self.debug_enabled:
                print(f"\n  === Creating Question (Internal) ===")
                print(f"  Raw Data: {question_data}")

            # Ensure pack_id is a valid UUID string
            pack_id_uuid = ensure_uuid(question_data.get("pack_id"))
            if not pack_id_uuid:
                 logger.error("Missing or invalid pack_id in question data")
                 return None

            # Map difficulty string/enum to enum for the model
            difficulty_initial_val = question_data.get("difficulty_initial")
            difficulty_current_val = question_data.get("difficulty_current")

            try:
                difficulty_initial_enum = DifficultyLevel(difficulty_initial_val.lower()) if difficulty_initial_val else None
                difficulty_current_enum = DifficultyLevel(difficulty_current_val.lower()) if difficulty_current_val else None
            except ValueError:
                logger.warning(f"Invalid difficulty value found: initial='{difficulty_initial_val}', current='{difficulty_current_val}'. Defaulting.")
                difficulty_initial_enum = DifficultyLevel.MIXED # Or handle as error
                difficulty_current_enum = DifficultyLevel.MIXED

            # Create Pydantic model for validation and structure
            question_create = QuestionCreate(
                question=question_data["question"],
                answer=question_data["answer"],
                pack_id=pack_id_uuid,
                pack_topics_item=question_data.get("pack_topics_item"),
                difficulty_initial=difficulty_initial_enum,
                difficulty_current=difficulty_current_enum or difficulty_initial_enum, # Default current to initial if missing
                correct_answer_rate=question_data.get("correct_answer_rate", 0.0)
            )

            if self.debug_enabled:
                print(f"  Prepared Schema: {question_create.model_dump(mode='json')}") # Use mode='json' for enum values

            created_question = await self.question_repository.create(obj_in=question_create)

            if self.debug_enabled:
                 print(f"  Database Result ID: {created_question.id if created_question else 'None'}")

            return created_question

        except Exception as e:
            logger.error(f"Error creating question internally: {str(e)}", exc_info=True)
            if self.debug_enabled:
                print(f"  Error creating question: {str(e)}")
                print(traceback.format_exc())
            return None


    async def _generate_questions_for_single_topic(
        self,
        pack_id: str,
        creation_name: str,
        topic_config: TopicQuestionConfig,
        difficulty_descriptions: Dict,
        seed_questions: Dict,
        debug_mode: bool
    ) -> List[Question]:
        """
        Internal helper to generate and store questions for ONE topic.
        Returns the list of successfully created Question objects.
        """
        pack_id_uuid = ensure_uuid(pack_id) # Ensure ID is UUID string
        if debug_mode:
            print(f"\n  Starting generation for topic: {topic_config.topic} (Difficulty: {topic_config.difficulty.value})")

        try:
            # --- Call the QuestionGenerator ---
            # The generator should return a list of dictionaries representing questions
            question_data_list: List[Dict] = await self.question_generator.generate_questions(
                pack_id=pack_id_uuid, # Pass UUID string
                creation_name=creation_name,
                pack_topic=topic_config.topic,
                difficulty=topic_config.difficulty, # Pass Enum directly
                difficulty_descriptions=difficulty_descriptions,
                seed_questions=seed_questions, # Pass relevant seeds
                num_questions=topic_config.num_questions,
                debug_mode=debug_mode,
                custom_instructions=topic_config.custom_instructions # Use topic-specific instructions
            )

            if debug_mode:
                print(f"  LLM generated {len(question_data_list)} raw question data items for topic '{topic_config.topic}'.")
                if question_data_list: print_json(question_data_list[0]) # Print first item example

            # --- Store the questions ---
            created_questions: List[Question] = []
            for q_data in question_data_list:
                # Add pack_id if missing (generator should ideally include it)
                if "pack_id" not in q_data:
                    q_data["pack_id"] = pack_id_uuid
                # Add topic if missing
                if "pack_topics_item" not in q_data:
                     q_data["pack_topics_item"] = topic_config.topic
                # Ensure difficulty is set
                if "difficulty_initial" not in q_data:
                     q_data["difficulty_initial"] = topic_config.difficulty
                if "difficulty_current" not in q_data:
                     q_data["difficulty_current"] = topic_config.difficulty

                # Call internal helper to create
                question_obj = await self._create_question(q_data)
                if question_obj:
                    created_questions.append(question_obj)

            if debug_mode:
                 print(f"  Successfully created {len(created_questions)} Question objects in DB for topic '{topic_config.topic}'.")

            return created_questions

        except Exception as e:
            logger.error(f"Error generating questions for topic '{topic_config.topic}': {str(e)}", exc_info=True)
            if debug_mode:
                print(f"  ERROR generating questions for topic '{topic_config.topic}': {str(e)}")
                print(traceback.format_exc())
            # Return empty list on failure for this specific topic
            return []

    async def generate_and_store_questions(
        self,
        pack_id: str,
        creation_name: str,
        pack_topic: str,
        difficulty: DifficultyLevel,
        num_questions: int = 5,
        debug_mode: bool = False,
        custom_instructions: Optional[str] = None
    ) -> List[Question]:
        """
        Generate questions for a SINGLE topic and store them.
        This method is called by the single-topic API endpoint.
        It now returns the list of created Question objects.
        Incorrect answer generation is handled separately by the API layer.
        """
        self.debug_enabled = debug_mode
        pack_id_uuid = ensure_uuid(pack_id)

        if self.debug_enabled:
            print(f"\n=== Starting Single Topic Question Generation (Service) ===")
            print(f"Pack ID: {pack_id_uuid}")
            print(f"Topic: {pack_topic}")
            print(f"Difficulty: {difficulty.value}")
            print(f"Number: {num_questions}")

        # Retrieve shared data (descriptions, seeds)
        difficulty_descriptions = {}
        seed_questions = {}
        if self.pack_creation_data_repository:
            try:
                creation_data = await self.pack_creation_data_repository.get_by_pack_id(pack_id_uuid)
                if creation_data:
                    difficulty_descriptions = creation_data.custom_difficulty_description or {}
                    seed_questions = creation_data.seed_questions or {}
            except Exception as e:
                logger.error(f"Error retrieving pack creation data for single topic generation: {e}")

        # Use the helper method for the core logic
        topic_config = TopicQuestionConfig(
            topic=pack_topic,
            num_questions=num_questions,
            difficulty=difficulty,
            custom_instructions=custom_instructions
        )

        created_questions = await self._generate_questions_for_single_topic(
            pack_id=pack_id_uuid,
            creation_name=creation_name,
            topic_config=topic_config,
            difficulty_descriptions=difficulty_descriptions,
            seed_questions=seed_questions.get(pack_topic, {}), # Get seeds for this specific topic
            debug_mode=debug_mode
        )

        # Return the list of created Question objects.
        # The API layer will handle triggering incorrect answer generation.
        return created_questions


    async def batch_generate_and_store_questions(
        self,
        pack_id: str,
        creation_name: str,
        topic_configs: List[TopicQuestionConfig],
        debug_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Generate questions for multiple topics concurrently and store them.
        Returns a summary dictionary including the list of created Question objects.
        Incorrect answer generation is handled separately by the API layer.
        """
        self.debug_enabled = debug_mode
        pack_id_uuid = ensure_uuid(pack_id)
        logger.info(f"Starting batch question generation for pack {pack_id_uuid} across {len(topic_configs)} topics.")

        # 1. Fetch shared data (difficulty descriptions, seeds) ONCE
        difficulty_descriptions = {}
        all_seed_questions = {} # Store all seeds, keyed by topic if needed later
        if self.pack_creation_data_repository:
            try:
                creation_data = await self.pack_creation_data_repository.get_by_pack_id(pack_id_uuid)
                if creation_data:
                    difficulty_descriptions = creation_data.custom_difficulty_description or {}
                    all_seed_questions = creation_data.seed_questions or {}
            except Exception as e:
                logger.error(f"Error retrieving pack creation data for batch generation: {e}")

        # 2. Create concurrent tasks for each topic
        tasks = []
        for config in topic_configs:
            # Get seeds relevant to the current topic (simple heuristic)
            topic_seeds = {q: a for q, a in all_seed_questions.items() if config.topic.lower() in q.lower()}
            if not topic_seeds: topic_seeds = all_seed_questions # Fallback

            task = asyncio.create_task(
                self._generate_questions_for_single_topic(
                    pack_id=pack_id_uuid,
                    creation_name=creation_name,
                    topic_config=config,
                    difficulty_descriptions=difficulty_descriptions,
                    seed_questions=topic_seeds,
                    debug_mode=debug_mode
                ),
                name=f"Generate_{config.topic}" # Name task for easier debugging
            )
            tasks.append(task)

        # 3. Run tasks concurrently and gather results
        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        # 4. Process results
        all_generated_questions: List[Question] = []
        successful_topics: List[str] = []
        failed_topics: List[str] = []
        total_generated_count = 0

        for i, result in enumerate(results_list):
            topic_name = topic_configs[i].topic
            if isinstance(result, Exception):
                failed_topics.append(topic_name)
                logger.error(f"Topic '{topic_name}' generation failed: {result}", exc_info=result)
                if debug_mode: print(f"  Topic '{topic_name}' FAILED: {result}")
            elif isinstance(result, list): # Expecting list of Question objects
                successful_topics.append(topic_name)
                all_generated_questions.extend(result)
                total_generated_count += len(result)
                if debug_mode: print(f"  Topic '{topic_name}' SUCCEEDED, added {len(result)} questions.")
            else:
                # This case indicates an issue with _generate_questions_for_single_topic return type
                failed_topics.append(topic_name)
                logger.error(f"Topic '{topic_name}' generation returned unexpected type: {type(result)}")
                if debug_mode: print(f"  Topic '{topic_name}' FAILED (unexpected return type: {type(result)})")


        logger.info(f"Batch generation finished for pack {pack_id_uuid}. Success: {len(successful_topics)}, Failed: {len(failed_topics)}, Total Questions: {total_generated_count}")

        # Return results including the list of generated Question objects
        # The API layer will use "generated_questions" to trigger incorrect answer generation.
        return {
            "success_topics": successful_topics,
            "failed_topics": failed_topics,
            "total_generated": total_generated_count,
            "generated_questions": all_generated_questions
        }

    # --- Other methods ---
    async def get_questions_by_pack_id(self, pack_id: str) -> List[Question]:
        """
        Retrieve all questions for a specific pack.
        """
        pack_id_uuid = ensure_uuid(pack_id)
        return await self.question_repository.get_by_pack_id(pack_id_uuid)

    async def get_questions_by_topic(self, pack_id: str, topic: str) -> List[Question]:
        """
        Retrieve questions for a specific pack filtered by topic.
        """
        pack_id_uuid = ensure_uuid(pack_id)
        all_questions = await self.question_repository.get_by_pack_id(pack_id_uuid)
        # Case-insensitive topic matching might be useful
        topic_lower = topic.lower()
        return [q for q in all_questions if q.pack_topics_item and q.pack_topics_item.lower() == topic_lower]

    async def update_question_statistics(
        self,
        question_id: str,
        correct: bool
    ) -> Optional[Question]:
        """
        Update question statistics based on user answer.
        (This logic seems fine and doesn't need changes for batch generation)
        """
        question_id_uuid = ensure_uuid(question_id)
        question = await self.question_repository.get_by_id(question_id_uuid)
        if not question:
            return None

        weight = 0.1
        new_rate = question.correct_answer_rate * (1 - weight) + (1.0 if correct else 0.0) * weight

        new_difficulty = self._adjust_difficulty_based_on_rate(
            question.difficulty_current,
            new_rate,
            question.difficulty_initial
        )

        update_data = QuestionUpdate(correct_answer_rate=new_rate)
        if new_difficulty != question.difficulty_current:
             update_data.difficulty_current = new_difficulty

        return await self.question_repository.update(id=question_id_uuid, obj_in=update_data)

    def _adjust_difficulty_based_on_rate(
        self,
        current_difficulty: Optional[DifficultyLevel],
        correct_rate: float,
        initial_difficulty: Optional[DifficultyLevel]
    ) -> Optional[DifficultyLevel]:
        """Adjust difficulty based on correct answer rate."""
        if not current_difficulty: return None # Keep None if it was None

        # Simple rules (can be refined)
        if current_difficulty == DifficultyLevel.EASY and correct_rate > 0.90: return DifficultyLevel.MEDIUM
        if current_difficulty == DifficultyLevel.MEDIUM:
            if correct_rate > 0.85: return DifficultyLevel.HARD
            if correct_rate < 0.40: return DifficultyLevel.EASY
        if current_difficulty == DifficultyLevel.HARD:
            if correct_rate > 0.80: return DifficultyLevel.EXPERT
            if correct_rate < 0.35: return DifficultyLevel.MEDIUM
        if current_difficulty == DifficultyLevel.EXPERT and correct_rate < 0.30: return DifficultyLevel.HARD

        return current_difficulty # No change