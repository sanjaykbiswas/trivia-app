# backend/src/services/incorrect_answer_service.py
import logging
from typing import List, Optional, Dict, Any
import asyncio

from ..models.question import Question
from ..models.incorrect_answers import IncorrectAnswers, IncorrectAnswersCreate, IncorrectAnswersUpdate
from ..repositories.question_repository import QuestionRepository
from ..repositories.incorrect_answers_repository import IncorrectAnswersRepository
from ..utils.question_generation.incorrect_answer_generator import IncorrectAnswerGenerator, IncorrectAnswerGenerationError # Import the custom error
from ..utils import ensure_uuid

logger = logging.getLogger(__name__)

class IncorrectAnswerService:
    """
    Service for generating and managing incorrect answers for trivia questions.
    """

    def __init__(
        self,
        question_repository: QuestionRepository,
        incorrect_answers_repository: IncorrectAnswersRepository,
        incorrect_answer_generator: Optional[IncorrectAnswerGenerator] = None
    ):
        self.question_repository = question_repository
        self.incorrect_answers_repository = incorrect_answers_repository
        self.incorrect_answer_generator = incorrect_answer_generator or IncorrectAnswerGenerator()

    async def generate_and_store_incorrect_answers(
        self,
        questions: List[Question], # Accepts List[Question]
        num_incorrect_answers: int = 3,
        batch_size: int = 5,
        debug_mode: bool = False
    ) -> Dict[str, List[str]]:
        """
        Generate incorrect answers for a list of questions and store them.
        Handles potential errors from the generator.

        Args:
            questions: List of Question objects
            num_incorrect_answers: Number of incorrect answers per question
            batch_size: Size of question batches for processing
            debug_mode: Enable verbose debug logging

        Returns:
            Dictionary mapping successfully processed question IDs (as strings)
            to their incorrect answers.

        Raises:
             IncorrectAnswerGenerationError: If generation fails definitively for
                                             one or more questions after retries.
        """
        if not questions:
            logger.warning("No questions provided for incorrect answer generation")
            return {}

        generation_results: List[Tuple[str, List[str]]] = [] # Expects (id_str, answers_list)
        failed_question_ids_from_gen: List[str] = []

        try:
            # Generate incorrect answers using the generator which might raise an error
            # The generator now returns List[Tuple[str, List[str]]] only for successes
            generation_results = await self.incorrect_answer_generator.generate_incorrect_answers(
                questions=questions,
                num_incorrect_answers=num_incorrect_answers,
                batch_size=batch_size,
                max_retries=1, # Allow one retry
                debug_mode=debug_mode
            )
            # If no exception, generation was successful for all questions attempted in the final retry.

        except IncorrectAnswerGenerationError as e:
            # Log the error and the IDs that failed definitively during generation
            logger.error(f"Incorrect answer generation failed permanently for some questions: {e.message}")
            failed_question_ids_from_gen = e.failed_question_ids
            # Continue to store results for questions that *did* succeed in generation_results

        # --- Store the successfully generated incorrect answers ---
        stored_answers_map: Dict[str, List[str]] = {}
        tasks_to_store = []

        for question_id_str, incorrect_answers in generation_results:
            # Create a task for each DB operation
             tasks_to_store.append(
                 asyncio.create_task(
                     self._store_single_incorrect_answer_set(question_id_str, incorrect_answers)
                 )
             )

        # Run storage operations concurrently
        storage_results = await asyncio.gather(*tasks_to_store, return_exceptions=True)

        # Process storage results
        db_failed_ids = []
        for i, result in enumerate(storage_results):
             question_id_str = generation_results[i][0] # Get corresponding ID
             if isinstance(result, Exception):
                 db_failed_ids.append(question_id_str)
                 logger.error(f"Database error storing incorrect answers for question {question_id_str}: {result}", exc_info=result)
             elif result: # If _store_single returned True
                  stored_answers_map[question_id_str] = generation_results[i][1] # Store the answers

        # --- Consolidate failures and potentially raise error ---
        final_failed_ids = list(set(failed_question_ids_from_gen + db_failed_ids))
        total_attempted_count = len(questions)
        final_successful_count = len(stored_answers_map)
        final_failed_count = total_attempted_count - final_successful_count

        logger.info(f"Finished storing incorrect answers. Success: {final_successful_count}/{total_attempted_count}. Failed (gen or store): {final_failed_count}")

        # If there were any definitive failures (either in generation or storage), raise exception
        if final_failed_ids:
             # Ensure we only report IDs that were actually in the input list
             original_ids_str = {str(q.id) for q in questions}
             actual_failures = list(set(final_failed_ids).intersection(original_ids_str))
             if actual_failures:
                 raise IncorrectAnswerGenerationError(
                     f"Failed to generate or store incorrect answers for {len(actual_failures)} questions.",
                     actual_failures
                 )

        return stored_answers_map # Return map of successfully stored answers

    async def _store_single_incorrect_answer_set(self, question_id_str: str, incorrect_answers: List[str]) -> bool:
        """Helper coroutine to store answers for one question."""
        question_id_uuid = ensure_uuid(question_id_str) # Ensure UUID string format
        try:
            existing_answers = await self.incorrect_answers_repository.get_by_question_id(question_id_uuid)
            if existing_answers:
                update_schema = IncorrectAnswersUpdate(incorrect_answers=incorrect_answers)
                update_result = await self.incorrect_answers_repository.update(
                    id=existing_answers.id, obj_in=update_schema
                )
                if update_result:
                    logger.debug(f"Updated incorrect answers for question {question_id_str}")
                    return True
                else:
                    logger.error(f"Failed to update incorrect answers DB record for question {question_id_str}")
                    return False
            else:
                create_data = IncorrectAnswersCreate(
                    question_id=question_id_uuid,
                    incorrect_answers=incorrect_answers
                )
                created = await self.incorrect_answers_repository.create(obj_in=create_data)
                if created:
                    logger.debug(f"Created incorrect answers for question {question_id_str}")
                    return True
                else:
                    logger.error(f"Failed to create incorrect answers DB record for question {question_id_str}")
                    return False
        except Exception as db_error:
             # Let the exception propagate up to be caught by gather
             raise db_error


    async def generate_for_pack(
        self,
        pack_id: str,
        num_incorrect_answers: int = 3,
        batch_size: int = 5,
        debug_mode: bool = False
    ) -> Dict[str, List[str]]:
        """
        Generate incorrect answers for all questions currently in a pack.
        """
        pack_id_uuid = ensure_uuid(pack_id)
        questions_in_pack = await self.question_repository.get_by_pack_id(pack_id_uuid)

        if not questions_in_pack:
            logger.warning(f"No questions found in pack {pack_id} to generate incorrect answers for.")
            return {}

        logger.info(f"Generating incorrect answers for {len(questions_in_pack)} questions in pack {pack_id}")

        # Call the core method that handles generation and storage
        # This will raise IncorrectAnswerGenerationError if generation fails for some questions
        # The API layer will catch this and report the failure.
        result_map = await self.generate_and_store_incorrect_answers(
            questions=questions_in_pack,
            num_incorrect_answers=num_incorrect_answers,
            batch_size=batch_size,
            debug_mode=debug_mode
        )
        return result_map # Returns dict of successes if no exception was raised


    async def get_incorrect_answers(
        self,
        question_id: str
    ) -> Optional[List[str]]:
        """
        Get incorrect answers for a specific question.
        """
        question_id_uuid = ensure_uuid(question_id)
        result = await self.incorrect_answers_repository.get_by_question_id(question_id_uuid)
        return result.incorrect_answers if result else None