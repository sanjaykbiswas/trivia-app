# backend/src/services/incorrect_answer_service.py
"""
Service for managing incorrect answers generation and storage.
"""
import logging
from typing import List, Optional, Dict

from ..models.question import Question
from ..models.incorrect_answers import IncorrectAnswers, IncorrectAnswersCreate
from ..repositories.question_repository import QuestionRepository
from ..repositories.incorrect_answers_repository import IncorrectAnswersRepository
from ..utils.question_generation.incorrect_answer_generator import IncorrectAnswerGenerator
from ..utils import ensure_uuid

# Configure logger
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
        """
        Initialize with required repositories and utilities.
        
        Args:
            question_repository: Repository for question operations
            incorrect_answers_repository: Repository for incorrect answers operations
            incorrect_answer_generator: Generator for incorrect answers. If None, creates a new instance.
        """
        self.question_repository = question_repository
        self.incorrect_answers_repository = incorrect_answers_repository
        self.incorrect_answer_generator = incorrect_answer_generator or IncorrectAnswerGenerator()
    
    async def generate_and_store_incorrect_answers(
        self,
        questions: List[Question],
        num_incorrect_answers: int = 3,
        batch_size: int = 5,
        debug_mode: bool = False
    ) -> Dict[str, IncorrectAnswers]:
        """
        Generate incorrect answers for questions and store them in the database.
        
        Args:
            questions: List of Question objects
            num_incorrect_answers: Number of incorrect answers to generate per question
            batch_size: Size of question batches for processing
            debug_mode: Enable verbose debug logging
            
        Returns:
            Dictionary mapping question IDs to their stored IncorrectAnswers
        """
        if not questions:
            logger.warning("No questions provided for incorrect answer generation")
            return {}
        
        # Generate incorrect answers
        generation_results = await self.incorrect_answer_generator.generate_incorrect_answers(
            questions=questions,
            num_incorrect_answers=num_incorrect_answers,
            batch_size=batch_size,
            debug_mode=debug_mode
        )
        
        # Store the generated incorrect answers
        stored_answers = {}
        
        for question_id, incorrect_answers in generation_results:
            # Ensure question_id is a valid UUID string
            question_id = ensure_uuid(question_id)
            
            # Check if we already have incorrect answers for this question
            existing_answers = await self.incorrect_answers_repository.get_by_question_id(question_id)
            
            if existing_answers:
                # Update existing incorrect answers
                update_result = await self.incorrect_answers_repository.update(
                    id=existing_answers.id,
                    obj_in={"incorrect_answers": incorrect_answers}
                )
                
                if update_result:
                    stored_answers[question_id] = update_result
                    logger.info(f"Updated incorrect answers for question {question_id}")
                else:
                    logger.error(f"Failed to update incorrect answers for question {question_id}")
            else:
                # Create new incorrect answers
                create_data = IncorrectAnswersCreate(
                    question_id=question_id,
                    incorrect_answers=incorrect_answers
                )
                
                created = await self.incorrect_answers_repository.create(obj_in=create_data)
                
                if created:
                    stored_answers[question_id] = created
                    logger.info(f"Created incorrect answers for question {question_id}")
                else:
                    logger.error(f"Failed to create incorrect answers for question {question_id}")
        
        logger.info(f"Stored incorrect answers for {len(stored_answers)}/{len(questions)} questions")
        return stored_answers
    
    async def generate_for_pack(
        self,
        pack_id: str,
        num_incorrect_answers: int = 3,
        batch_size: int = 5,
        debug_mode: bool = False
    ) -> Dict[str, IncorrectAnswers]:
        """
        Generate incorrect answers for all questions in a pack.
        
        Args:
            pack_id: ID of the pack
            num_incorrect_answers: Number of incorrect answers to generate per question
            batch_size: Size of question batches for processing
            debug_mode: Enable verbose debug logging
            
        Returns:
            Dictionary mapping question IDs to their stored IncorrectAnswers
        """
        # Ensure pack_id is a valid UUID string
        pack_id = ensure_uuid(pack_id)
        
        # Get all questions for the pack
        questions = await self.question_repository.get_by_pack_id(pack_id)
        
        if not questions:
            logger.warning(f"No questions found for pack {pack_id}")
            return {}
        
        logger.info(f"Generating incorrect answers for {len(questions)} questions in pack {pack_id}")
        
        return await self.generate_and_store_incorrect_answers(
            questions=questions,
            num_incorrect_answers=num_incorrect_answers,
            batch_size=batch_size,
            debug_mode=debug_mode
        )
    
    async def get_incorrect_answers(
        self,
        question_id: str
    ) -> Optional[IncorrectAnswers]:
        """
        Get incorrect answers for a specific question.
        
        Args:
            question_id: ID of the question
            
        Returns:
            IncorrectAnswers object or None if not found
        """
        # Ensure question_id is a valid UUID string
        question_id = ensure_uuid(question_id)
        
        return await self.incorrect_answers_repository.get_by_question_id(question_id)