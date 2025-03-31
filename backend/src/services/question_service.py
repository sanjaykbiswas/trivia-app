# backend/src/services/question_service.py
import uuid
import logging
from typing import List, Dict, Any, Optional, Union, Tuple

from ..models.question import Question, QuestionCreate, QuestionUpdate, DifficultyLevel
from ..models.incorrect_answers import IncorrectAnswers, IncorrectAnswersCreate
from ..repositories.question_repository import QuestionRepository
from ..repositories.incorrect_answers_repository import IncorrectAnswersRepository
from ..repositories.pack_creation_data_repository import PackCreationDataRepository
from ..utils.question_generation.question_generator import QuestionGenerator
from ..utils import ensure_uuid

# Configure logger
logger = logging.getLogger(__name__)

class QuestionService:
    """
    Service for question management operations.
    
    Handles business logic related to creating, retrieving,
    and managing trivia questions and their incorrect answers.
    """
    
    def __init__(
        self,
        question_repository: QuestionRepository,
        incorrect_answers_repository: IncorrectAnswersRepository,
        pack_creation_data_repository: Optional[PackCreationDataRepository] = None,
        question_generator: Optional[QuestionGenerator] = None
    ):
        """
        Initialize the service with required repositories.
        
        Args:
            question_repository: Repository for question operations
            incorrect_answers_repository: Repository for incorrect answers operations
            pack_creation_data_repository: Optional repository for accessing pack metadata
            question_generator: Optional question generator utility
        """
        self.question_repository = question_repository
        self.incorrect_answers_repository = incorrect_answers_repository
        self.pack_creation_data_repository = pack_creation_data_repository
        self.question_generator = question_generator or QuestionGenerator()
    
    async def generate_and_store_questions(
        self,
        pack_id: uuid.UUID,
        creation_name: str,
        pack_topic: str,
        difficulty: Union[str, DifficultyLevel],
        num_questions: int = 5,
        incorrect_answers_per_question: int = 3
    ) -> List[Question]:
        """
        Generate questions using LLM and store them in the database.
        
        Args:
            pack_id: UUID of the pack
            creation_name: Name of the trivia pack
            pack_topic: Specific topic to generate questions for
            difficulty: Difficulty level for questions
            num_questions: Number of questions to generate
            incorrect_answers_per_question: Number of incorrect answers to generate per question
            
        Returns:
            List of created Question objects
        """
        # Ensure pack_id is a proper UUID object
        pack_id = ensure_uuid(pack_id)
        
        # Retrieve difficulty descriptions if pack_creation_data_repository is provided
        difficulty_descriptions = {}
        seed_questions = {}
        
        if self.pack_creation_data_repository:
            # Fetch pack creation data
            creation_data = await self.pack_creation_data_repository.get_by_pack_id(pack_id)
            if creation_data:
                # Get difficulty descriptions
                difficulty_descriptions = creation_data.custom_difficulty_description
                # Get seed questions if available
                seed_questions = creation_data.seed_questions
        
        # Generate questions using the utility
        question_data_list = await self.question_generator.generate_questions(
            pack_id=pack_id,
            creation_name=creation_name,
            pack_topic=pack_topic,
            difficulty=difficulty,
            difficulty_descriptions=difficulty_descriptions,
            seed_questions=seed_questions,
            num_questions=num_questions
        )
        
        # Store the questions
        created_questions = []
        for question_data in question_data_list:
            # Create the question
            question_obj = await self._create_question(question_data)
            
            # Generate and store incorrect answers
            if question_obj:
                await self._generate_and_store_incorrect_answers(
                    question_obj,
                    num_incorrect_answers=incorrect_answers_per_question
                )
                created_questions.append(question_obj)
        
        return created_questions
    
    async def _create_question(self, question_data: Dict[str, Any]) -> Optional[Question]:
        """
        Create a question in the database.
        
        Args:
            question_data: Dictionary containing question data
            
        Returns:
            Created Question object or None if creation failed
        """
        try:
            # Prepare question create schema
            question_create = QuestionCreate(
                question=question_data["question"],
                answer=question_data["answer"],
                pack_id=question_data["pack_id"],
                pack_topics_item=question_data.get("pack_topics_item"),
                difficulty_initial=question_data.get("difficulty_initial"),
                difficulty_current=question_data.get("difficulty_current"),
                correct_answer_rate=question_data.get("correct_answer_rate", 0.0)
            )
            
            # Create the question in the database
            return await self.question_repository.create(obj_in=question_create)
            
        except Exception as e:
            logger.error(f"Error creating question: {str(e)}")
            return None
    
    async def _generate_and_store_incorrect_answers(
        self,
        question: Question,
        num_incorrect_answers: int = 3
    ) -> Optional[IncorrectAnswers]:
        """
        Generate incorrect answers for a question and store them.
        
        Args:
            question: Question object to generate incorrect answers for
            num_incorrect_answers: Number of incorrect answers to generate
            
        Returns:
            Created IncorrectAnswers object or None if creation failed
        """
        try:
            # In a real implementation, we would use LLM to generate plausible
            # incorrect answers based on the question and correct answer
            
            # For now, use placeholder incorrect answers
            incorrect_answers = [
                f"Incorrect answer {i+1} for '{question.question}'" 
                for i in range(num_incorrect_answers)
            ]
            
            # Create incorrect answers schema
            incorrect_answers_create = IncorrectAnswersCreate(
                incorrect_answers=incorrect_answers,
                question_id=question.id
            )
            
            # Store in the database
            return await self.incorrect_answers_repository.create(obj_in=incorrect_answers_create)
            
        except Exception as e:
            logger.error(f"Error creating incorrect answers: {str(e)}")
            return None
    
    async def get_questions_by_pack_id(self, pack_id: uuid.UUID) -> List[Question]:
        """
        Retrieve all questions for a specific pack.
        
        Args:
            pack_id: UUID of the pack
            
        Returns:
            List of Question objects
        """
        # Ensure pack_id is a proper UUID object
        pack_id = ensure_uuid(pack_id)
        
        # Use the repository to get questions
        return await self.question_repository.get_by_pack_id(pack_id)
    
    async def get_questions_by_topic(self, pack_id: uuid.UUID, topic: str) -> List[Question]:
        """
        Retrieve questions for a specific pack filtered by topic.
        
        Args:
            pack_id: UUID of the pack
            topic: Topic to filter by
            
        Returns:
            List of Question objects
        """
        # Ensure pack_id is a proper UUID object
        pack_id = ensure_uuid(pack_id)
        
        # Get all questions for the pack
        all_questions = await self.question_repository.get_by_pack_id(pack_id)
        
        # Filter by topic
        return [q for q in all_questions if q.pack_topics_item == topic]
    
    async def get_question_with_incorrect_answers(
        self,
        question_id: uuid.UUID
    ) -> Tuple[Optional[Question], List[str]]:
        """
        Retrieve a question and its incorrect answers.
        
        Args:
            question_id: UUID of the question
            
        Returns:
            Tuple containing:
                - Question object or None if not found
                - List of incorrect answer strings
        """
        # Ensure question_id is a proper UUID object
        question_id = ensure_uuid(question_id)
        
        # Get the question
        question = await self.question_repository.get_by_id(question_id)
        if not question:
            return None, []
        
        # Get incorrect answers
        incorrect_answers_obj = await self.incorrect_answers_repository.get_by_question_id(question_id)
        
        if incorrect_answers_obj:
            return question, incorrect_answers_obj.incorrect_answers
        else:
            return question, []
    
    async def update_question_statistics(
        self,
        question_id: uuid.UUID,
        correct: bool
    ) -> Optional[Question]:
        """
        Update question statistics based on user answer.
        
        Args:
            question_id: UUID of the question
            correct: Whether the user answered correctly
            
        Returns:
            Updated Question object or None if update failed
        """
        # Ensure question_id is a proper UUID object
        question_id = ensure_uuid(question_id)
        
        # Get the question
        question = await self.question_repository.get_by_id(question_id)
        if not question:
            return None
        
        # Recalculate correct answer rate
        # This is a simple weighted average approach
        # In a real implementation, you might want a more sophisticated algorithm
        weight = 0.1  # Weight for the new data point
        new_rate = question.correct_answer_rate * (1 - weight) + (1.0 if correct else 0.0) * weight
        
        # Update difficulty based on correct answer rate if needed
        new_difficulty = self._adjust_difficulty_based_on_rate(
            question.difficulty_current,
            new_rate,
            question.difficulty_initial
        )
        
        # Update the question
        return await self.question_repository.update_statistics(
            question_id=question_id,
            correct_rate=new_rate,
            new_difficulty=new_difficulty
        )
    
    def _adjust_difficulty_based_on_rate(
        self,
        current_difficulty: Optional[DifficultyLevel],
        correct_rate: float,
        initial_difficulty: Optional[DifficultyLevel]
    ) -> Optional[DifficultyLevel]:
        """
        Adjust difficulty based on correct answer rate.
        
        Args:
            current_difficulty: Current difficulty level
            correct_rate: Current correct answer rate
            initial_difficulty: Initial difficulty level
            
        Returns:
            New difficulty level or None if no change
        """
        # If no current difficulty, maintain that
        if not current_difficulty:
            return None
        
        # Simple rules for difficulty adjustment
        # In a real implementation, these thresholds would be configurable
        if current_difficulty == DifficultyLevel.EASY:
            if correct_rate > 0.90:
                return DifficultyLevel.MEDIUM
        elif current_difficulty == DifficultyLevel.MEDIUM:
            if correct_rate > 0.85:
                return DifficultyLevel.HARD
            elif correct_rate < 0.40:
                return DifficultyLevel.EASY
        elif current_difficulty == DifficultyLevel.HARD:
            if correct_rate > 0.80:
                return DifficultyLevel.EXPERT
            elif correct_rate < 0.35:
                return DifficultyLevel.MEDIUM
        elif current_difficulty == DifficultyLevel.EXPERT:
            if correct_rate < 0.30:
                return DifficultyLevel.HARD
        
        # No change
        return current_difficulty