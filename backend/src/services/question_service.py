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
# --- Import the new/modified schemas ---
from ..api.schemas.question import TopicQuestionConfig, DifficultyConfig
# --- End Import ---
from ..utils import ensure_uuid

# Configure logger
logger = logging.getLogger(__name__)

# Helper to print JSON nicely during debug
def print_json(data: Any):
    try:
        # Use model_dump for Pydantic V2 if applicable, otherwise default=str
        print(json.dumps(data, indent=2, default=lambda x: x.value if isinstance(x, DifficultyLevel) else str(x)))
    except Exception as e:
        print(f"Could not print JSON: {e}")
        print(data)

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
    ):
        """
        Initialize the service with required repositories.
        """
        self.question_repository = question_repository
        self.pack_creation_data_repository = pack_creation_data_repository
        self.question_generator = question_generator or QuestionGenerator()
        self.debug_enabled = False # Instance variable for debug mode

    async def _create_question(self, question_data: Dict[str, Any]) -> Optional[Question]:
        """
        Helper method to create a single question in the database.
        Validates data and uses the repository.
        (This is the corrected version from the previous step)
        """
        try:
            if self.debug_enabled:
                print("\n  === Creating Question (Internal) ===")
                print(f"  Raw Data: {question_data}")

            pack_id_uuid = ensure_uuid(question_data.get("pack_id"))
            if not pack_id_uuid:
                 logger.error("Missing or invalid pack_id in question data")
                 return None

            difficulty_initial_val = question_data.get("difficulty_initial")
            difficulty_current_val = question_data.get("difficulty_current")

            try:
                # Handle if value is already an enum or a string
                if isinstance(difficulty_initial_val, DifficultyLevel):
                     difficulty_initial_enum = difficulty_initial_val
                else:
                     difficulty_initial_enum = DifficultyLevel(difficulty_initial_val.lower()) if difficulty_initial_val else None

                if isinstance(difficulty_current_val, DifficultyLevel):
                     difficulty_current_enum = difficulty_current_val
                else:
                     difficulty_current_enum = DifficultyLevel(difficulty_current_val.lower()) if difficulty_current_val else None

            except (ValueError, AttributeError):
                logger.warning(f"Invalid difficulty value found: initial='{difficulty_initial_val}', current='{difficulty_current_val}'. Defaulting to MIXED.")
                difficulty_initial_enum = DifficultyLevel.MIXED
                difficulty_current_enum = DifficultyLevel.MIXED

            question_create = QuestionCreate(
                question=question_data["question"],
                answer=question_data["answer"],
                pack_id=pack_id_uuid,
                pack_topics_item=question_data.get("pack_topics_item"),
                difficulty_initial=difficulty_initial_enum,
                difficulty_current=difficulty_current_enum or difficulty_initial_enum,
                correct_answer_rate=question_data.get("correct_answer_rate", 0.0)
            )

            if self.debug_enabled:
                print(f"  Prepared Schema:")
                print_json(question_create.model_dump(mode='json'))

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

    # --- RENAMED and MODIFIED Helper for batch ---
    async def _generate_questions_for_topic_difficulty(
        self,
        pack_id: str,
        creation_name: str,
        topic: str,
        difficulty_config: DifficultyConfig,
        difficulty_descriptions: Dict,
        seed_questions: Dict,
        custom_instructions: Optional[str],
        debug_mode: bool
    ) -> List[Question]:
        """
        Internal helper to generate and store questions for ONE topic-difficulty pair.
        Returns the list of successfully created Question objects.
        (This is the corrected version from the previous step)
        """
        pack_id_uuid = ensure_uuid(pack_id)
        target_difficulty = difficulty_config.difficulty
        num_questions = difficulty_config.num_questions

        if debug_mode:
            print(f"\n  Starting generation for topic: '{topic}' (Difficulty: {target_difficulty.value}, Count: {num_questions})")

        try:
            # Call the QuestionGenerator
            question_data_list: List[Dict] = await self.question_generator.generate_questions(
                pack_id=pack_id_uuid,
                creation_name=creation_name,
                pack_topic=topic,
                difficulty=target_difficulty,
                difficulty_descriptions=difficulty_descriptions,
                seed_questions=seed_questions,
                num_questions=num_questions,
                debug_mode=debug_mode,
                custom_instructions=custom_instructions
            )

            if debug_mode:
                print(f"  LLM generated {len(question_data_list)} raw items for '{topic}' ({target_difficulty.value}).")
                if question_data_list: print_json(question_data_list[0])

            # Store the questions
            created_questions: List[Question] = []
            for q_data in question_data_list:
                if "pack_id" not in q_data: q_data["pack_id"] = pack_id_uuid
                if "pack_topics_item" not in q_data: q_data["pack_topics_item"] = topic
                q_data["difficulty_initial"] = target_difficulty
                q_data["difficulty_current"] = target_difficulty

                question_obj = await self._create_question(q_data)
                if question_obj:
                    created_questions.append(question_obj)

            if debug_mode:
                 print(f"  Successfully created {len(created_questions)} DB questions for '{topic}' ({target_difficulty.value}).")

            return created_questions

        except Exception as e:
            logger.error(f"Error generating questions for topic '{topic}', difficulty '{target_difficulty.value}': {str(e)}", exc_info=True)
            if debug_mode:
                print(f"  ERROR generating for '{topic}' ({target_difficulty.value}): {str(e)}")
                print(traceback.format_exc())
            return []
    # --- END RENAMED and MODIFIED Helper ---

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
        Generate questions for a SINGLE topic and SINGLE difficulty and store them.
        (This is the corrected version from the previous step)
        """
        self.debug_enabled = debug_mode # Set instance variable
        pack_id_uuid = ensure_uuid(pack_id)

        if self.debug_enabled:
            print(f"\n=== Starting Single Topic/Difficulty Question Generation (Service) ===")
            print(f"Pack ID: {pack_id_uuid}, Topic: {pack_topic}, Difficulty: {difficulty.value}, Count: {num_questions}")

        # Retrieve shared data
        difficulty_descriptions = {}
        seed_questions = {}
        if self.pack_creation_data_repository:
            try:
                creation_data = await self.pack_creation_data_repository.get_by_pack_id(pack_id_uuid)
                if creation_data:
                    difficulty_descriptions = creation_data.custom_difficulty_description or {}
                    all_seeds = creation_data.seed_questions or {}
                    seed_questions = {q: a for q, a in all_seeds.items() if pack_topic.lower() in q.lower()}
            except Exception as e:
                logger.error(f"Error retrieving pack creation data for single generation: {e}")

        difficulty_config = DifficultyConfig(
            difficulty=difficulty,
            num_questions=num_questions
        )

        # Use the specific helper for topic/difficulty pair
        created_questions = await self._generate_questions_for_topic_difficulty(
            pack_id=pack_id_uuid,
            creation_name=creation_name,
            topic=pack_topic,
            difficulty_config=difficulty_config,
            difficulty_descriptions=difficulty_descriptions,
            seed_questions=seed_questions,
            custom_instructions=custom_instructions,
            debug_mode=debug_mode
        )
        return created_questions

    # --- REWRITTEN batch generation method ---
    async def batch_generate_and_store_questions(
        self,
        pack_id: str,
        creation_name: str,
        topic_configs: List[TopicQuestionConfig], # Uses the NEW schema
        debug_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Generate questions concurrently for multiple topics AND multiple difficulties.
        Returns a summary dictionary including the list of created Question objects.
        (This is the corrected version from the previous step)
        """
        self.debug_enabled = debug_mode # Set instance variable
        pack_id_uuid = ensure_uuid(pack_id)
        logger.info(f"Starting batch generation for pack {pack_id_uuid} across multiple topics/difficulties.")
        if debug_mode:
            print(f"\n=== Starting Batch Question Generation (Service) ===")
            print(f"Pack ID: {pack_id_uuid}")
            print(f"Total Topic Configs: {len(topic_configs)}")

        # 1. Fetch shared data ONCE
        difficulty_descriptions = {}
        all_seed_questions = {}
        if self.pack_creation_data_repository:
            try:
                creation_data = await self.pack_creation_data_repository.get_by_pack_id(pack_id_uuid)
                if creation_data:
                    difficulty_descriptions = creation_data.custom_difficulty_description or {}
                    all_seed_questions = creation_data.seed_questions or {}
                    if debug_mode: print("  Fetched pack creation data (descriptions, seeds).")
            except Exception as e:
                logger.error(f"Error retrieving pack creation data for batch generation: {e}")
                if debug_mode: print("  Error fetching pack creation data.")

        # 2. Create concurrent tasks for EACH topic-difficulty pair
        tasks = []
        task_metadata = []
        total_tasks = 0
        for topic_config in topic_configs:
            topic = topic_config.topic
            topic_seeds = {q: a for q, a in all_seed_questions.items() if topic.lower() in q.lower()}
            topic_custom_instructions = topic_config.custom_instructions

            for difficulty_config in topic_config.difficulty_configs:
                task = asyncio.create_task(
                    self._generate_questions_for_topic_difficulty(
                        pack_id=pack_id_uuid, creation_name=creation_name, topic=topic,
                        difficulty_config=difficulty_config, difficulty_descriptions=difficulty_descriptions,
                        seed_questions=topic_seeds, custom_instructions=topic_custom_instructions,
                        debug_mode=debug_mode
                    ), name=f"Generate_{topic}_{difficulty_config.difficulty.value}"
                )
                tasks.append(task)
                task_metadata.append({"topic": topic, "difficulty": difficulty_config.difficulty.value})
                total_tasks += 1
        if debug_mode: print(f"  Created {total_tasks} generation tasks.")

        # 3. Run tasks concurrently and gather results
        if debug_mode: print("  Awaiting task completion...")
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        if debug_mode: print("  Tasks completed.")

        # 4. Process results
        all_generated_questions: List[Question] = []
        successful_topics: set[str] = set()
        failed_configs: List[Dict[str, Any]] = []
        total_generated_count = 0
        for i, result in enumerate(results_list):
            meta = task_metadata[i]
            topic_name = meta["topic"]
            difficulty_name = meta["difficulty"]
            if isinstance(result, Exception):
                failed_configs.append({**meta, "error": str(result)})
                logger.error(f"Task for Topic '{topic_name}' ({difficulty_name}) failed: {result}", exc_info=result)
                if debug_mode: print(f"  Task '{topic_name}' ({difficulty_name}) FAILED: {result}")
            elif isinstance(result, list):
                if result:
                     all_generated_questions.extend(result)
                     total_generated_count += len(result)
                     successful_topics.add(topic_name)
                     if debug_mode: print(f"  Task '{topic_name}' ({difficulty_name}) SUCCEEDED, added {len(result)} questions.")
                else:
                     logger.warning(f"Task for Topic '{topic_name}' ({difficulty_name}) generated 0 questions.")
                     failed_configs.append({**meta, "error": "Generated 0 questions"})
                     if debug_mode: print(f"  Task '{topic_name}' ({difficulty_name}) completed but generated 0 questions.")
            else:
                failed_configs.append({**meta, "error": f"Unexpected return type: {type(result)}"})
                logger.error(f"Task for Topic '{topic_name}' ({difficulty_name}) returned unexpected type: {type(result)}")
                if debug_mode: print(f"  Task '{topic_name}' ({difficulty_name}) FAILED (unexpected return type: {type(result)})")

        # Determine overall status
        final_status = "completed"
        failed_topic_names = list(set(fc['topic'] for fc in failed_configs))
        if failed_configs and len(successful_topics) == 0: final_status = "failed"
        elif failed_configs: final_status = "partial_failure"

        logger.info(f"Batch generation finished. Status: {final_status}. Success Topics: {len(successful_topics)}. Failed Configs: {len(failed_configs)}. Total Questions: {total_generated_count}")
        if debug_mode:
             print(f"Batch Summary: Status={final_status}, Success Topics={len(successful_topics)}, Failed Configs={len(failed_configs)}, Total Questions={total_generated_count}")
             if failed_configs: print_json({"Failed Configs Details": failed_configs})

        return {
            "topics_processed": list(successful_topics),
            "failed_topics": failed_topic_names,
            "total_generated": total_generated_count,
            "generated_questions": all_generated_questions
        }
    # --- END REWRITTEN ---

    # --- OTHER METHODS (Retrieval and Update - Added Back) ---
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
        topic_lower = topic.lower()
        return [q for q in all_questions if q.pack_topics_item and q.pack_topics_item.lower() == topic_lower]

    async def update_question_statistics(
        self,
        question_id: str,
        correct: bool
    ) -> Optional[Question]:
        """
        Update question statistics based on user answer.
        """
        question_id_uuid = ensure_uuid(question_id)
        question = await self.question_repository.get_by_id(question_id_uuid)
        if not question:
            return None

        weight = 0.1 # Simple moving average weight
        current_rate = question.correct_answer_rate if question.correct_answer_rate is not None else 0.5 # Default if None
        new_rate = current_rate * (1 - weight) + (1.0 if correct else 0.0) * weight

        new_difficulty = self._adjust_difficulty_based_on_rate(
            question.difficulty_current,
            new_rate,
            question.difficulty_initial
        )

        update_data = QuestionUpdate(correct_answer_rate=new_rate)
        # Only update difficulty if it actually changed
        if new_difficulty != question.difficulty_current:
             update_data.difficulty_current = new_difficulty

        # Make sure update_data is not empty before calling update
        if update_data.model_dump(exclude_unset=True):
             return await self.question_repository.update(id=question_id_uuid, obj_in=update_data)
        else:
            return question # Return original if no changes were made

    def _adjust_difficulty_based_on_rate(
        self,
        current_difficulty: Optional[DifficultyLevel],
        correct_rate: float,
        initial_difficulty: Optional[DifficultyLevel] # Keep initial for reference if needed
    ) -> Optional[DifficultyLevel]:
        """Adjust difficulty based on correct answer rate."""
        # Thresholds can be tuned
        EASY_UPPER = 0.90
        MEDIUM_UPPER = 0.85
        MEDIUM_LOWER = 0.40
        HARD_UPPER = 0.80
        HARD_LOWER = 0.35
        EXPERT_LOWER = 0.30

        if not current_difficulty: return None # Cannot adjust if not set

        # Promote based on high success rate
        if current_difficulty == DifficultyLevel.EASY and correct_rate > EASY_UPPER: return DifficultyLevel.MEDIUM
        if current_difficulty == DifficultyLevel.MEDIUM and correct_rate > MEDIUM_UPPER: return DifficultyLevel.HARD
        if current_difficulty == DifficultyLevel.HARD and correct_rate > HARD_UPPER: return DifficultyLevel.EXPERT
        # No promotion from Expert based on rate alone in this simple model

        # Demote based on low success rate
        if current_difficulty == DifficultyLevel.MEDIUM and correct_rate < MEDIUM_LOWER: return DifficultyLevel.EASY
        if current_difficulty == DifficultyLevel.HARD and correct_rate < HARD_LOWER: return DifficultyLevel.MEDIUM
        if current_difficulty == DifficultyLevel.EXPERT and correct_rate < EXPERT_LOWER: return DifficultyLevel.HARD
        # No demotion from Easy based on rate alone

        return current_difficulty # No change if no thresholds met