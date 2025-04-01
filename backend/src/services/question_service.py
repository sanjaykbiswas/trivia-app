# backend/src/services/question_service.py
import uuid
import logging
import json
import traceback
from typing import List, Dict, Any, Optional, Union, Tuple

from ..models.question import Question, QuestionCreate, QuestionUpdate, DifficultyLevel
from ..repositories.question_repository import QuestionRepository
from ..repositories.pack_creation_data_repository import PackCreationDataRepository
from ..utils.question_generation.question_generator import QuestionGenerator
from ..utils.question_generation.incorrect_answer_generator import IncorrectAnswerGenerator
from ..models.incorrect_answers import IncorrectAnswersCreate
from ..utils import ensure_uuid

# Configure logger
logger = logging.getLogger(__name__)

class QuestionService:
    """
    Service for question management operations.
    
    Handles business logic related to creating, retrieving,
    and managing trivia questions.
    """
    
    def __init__(
        self,
        question_repository: QuestionRepository,
        pack_creation_data_repository: Optional[PackCreationDataRepository] = None,
        question_generator: Optional[QuestionGenerator] = None,
        incorrect_answer_generator: Optional[IncorrectAnswerGenerator] = None
    ):
        """
        Initialize the service with required repositories.
        
        Args:
            question_repository: Repository for question operations
            pack_creation_data_repository: Optional repository for accessing pack metadata
            question_generator: Optional question generator utility
            incorrect_answer_generator: Optional incorrect answer generator utility
        """
        self.question_repository = question_repository
        self.pack_creation_data_repository = pack_creation_data_repository
        self.question_generator = question_generator or QuestionGenerator()
        self.incorrect_answer_generator = incorrect_answer_generator or IncorrectAnswerGenerator()
        self.debug_enabled = False
    
    async def generate_and_store_questions(
        self,
        pack_id: str,
        creation_name: str,
        pack_topic: str,
        difficulty: Union[str, DifficultyLevel],
        num_questions: int = 5,
        debug_mode: bool = False,
        custom_instructions: Optional[str] = None
    ) -> List[Question]:
        """
        Generate questions using LLM and store them in the database.
        
        Args:
            pack_id: ID of the pack
            creation_name: Name of the trivia pack
            pack_topic: Specific topic to generate questions for
            difficulty: Difficulty level for questions
            num_questions: Number of questions to generate
            debug_mode: Enable verbose debug output
            custom_instructions: Optional custom instructions for question generation
            
        Returns:
            List of created Question objects
        """
        self.debug_enabled = debug_mode
        
        if self.debug_enabled:
            print(f"\n=== Starting Question Generation and Storage ===")
            print(f"Pack ID: {pack_id}")
            print(f"Topic: {pack_topic}")
            print(f"Difficulty: {difficulty}")
            print(f"Number of questions: {num_questions}")
            if custom_instructions:
                print(f"Custom instructions: {custom_instructions}")
        
        # Ensure pack_id is a valid UUID string
        pack_id = ensure_uuid(pack_id)
        
        # Retrieve difficulty descriptions if pack_creation_data_repository is provided
        difficulty_descriptions = {}
        seed_questions = {}
        
        if self.pack_creation_data_repository:
            try:
                # Fetch pack creation data
                creation_data = await self.pack_creation_data_repository.get_by_pack_id(pack_id)
                if creation_data:
                    # Get difficulty descriptions
                    difficulty_descriptions = creation_data.custom_difficulty_description
                    # Get seed questions if available
                    seed_questions = creation_data.seed_questions
                    
                    if self.debug_enabled:
                        print("\n=== Pack Creation Data Retrieved ===")
                        print(f"Found difficulty descriptions: {bool(difficulty_descriptions)}")
                        print(f"Found seed questions: {len(seed_questions) if seed_questions else 0}")
            except Exception as e:
                logger.error(f"Error retrieving pack creation data: {str(e)}")
                if self.debug_enabled:
                    print(f"Error retrieving pack creation data: {str(e)}")
                    print(traceback.format_exc())
        
        try:
            # Generate questions using the utility with debug mode
            question_data_list = await self.question_generator.generate_questions(
                pack_id=pack_id,
                creation_name=creation_name,
                pack_topic=pack_topic,
                difficulty=difficulty,
                difficulty_descriptions=difficulty_descriptions,
                seed_questions=seed_questions,
                num_questions=num_questions,
                debug_mode=debug_mode,
                custom_instructions=custom_instructions
            )
            
            if self.debug_enabled:
                print(f"\n=== Generated Question Data ===")
                print(f"Number of questions generated: {len(question_data_list)}")
                # Safe JSON serialization for data display
                safe_data = []
                for q in question_data_list:
                    safe_q = q.copy()
                    safe_data.append(safe_q)
                
                if safe_data:
                    try:
                        print(f"First question data: {json.dumps(safe_data[0], indent=2)}")
                    except Exception as e:
                        print(f"Error displaying question data: {str(e)}")
                        print(f"Raw first question data: {safe_data[0] if safe_data else None}")
            
            # Store the questions
            created_questions = []
            for question_data in question_data_list:
                # Create the question
                question_obj = await self._create_question(question_data)
                if question_obj:
                    created_questions.append(question_obj)
            
            if self.debug_enabled:
                print(f"\n=== Question Storage Results ===")
                print(f"Questions successfully created: {len(created_questions)}/{len(question_data_list)}")
            
            # Generate incorrect answers for the created questions
            if created_questions:
                try:
                    incorrect_answers_results = await self.generate_incorrect_answers_for_questions(
                        questions=created_questions,
                        debug_mode=debug_mode
                    )
                    
                    # Store the incorrect answers
                    for question, incorrect_answers in incorrect_answers_results:
                        # Create incorrect answers record
                        if incorrect_answers:
                            # Get incorrect_answers_repository
                            incorrect_answers_repo = await self._get_incorrect_answers_repository()
                            
                            if incorrect_answers_repo:
                                incorrect_answers_data = IncorrectAnswersCreate(
                                    question_id=question.id,
                                    incorrect_answers=incorrect_answers
                                )
                                
                                await incorrect_answers_repo.create(obj_in=incorrect_answers_data)
                                
                                if self.debug_enabled:
                                    print(f"Stored {len(incorrect_answers)} incorrect answers for question {question.id}")
                except Exception as e:
                    logger.error(f"Error generating or storing incorrect answers: {str(e)}")
                    if self.debug_enabled:
                        print(f"Error generating or storing incorrect answers: {str(e)}")
            
            return created_questions
            
        except Exception as e:
            logger.error(f"Error in question generation and storage: {str(e)}")
            if self.debug_enabled:
                print(f"\n=== Error in Question Generation and Storage ===")
                print(f"Error: {str(e)}")
                print(traceback.format_exc())
            return []
    
    async def _create_question(self, question_data: Dict[str, Any]) -> Optional[Question]:
        """
        Create a question in the database.
        
        Args:
            question_data: Dictionary containing question data
            
        Returns:
            Created Question object or None if creation failed
        """
        try:
            # Debug: Print the question data before modification
            if self.debug_enabled:
                print(f"\n=== Creating Question ===")
                print(f"Question data: {question_data}")
            
            # Prepare question create schema
            question_create = QuestionCreate(
                question=question_data["question"],
                answer=question_data["answer"],
                pack_id=question_data["pack_id"],  # Already a string
                pack_topics_item=question_data.get("pack_topics_item"),
                difficulty_initial=question_data.get("difficulty_initial"),
                difficulty_current=question_data.get("difficulty_current"),
                correct_answer_rate=question_data.get("correct_answer_rate", 0.0)
            )
            
            if self.debug_enabled:
                print(f"Creating question in database with data:")
                print(f"Question: {question_create.question[:50]}...")
                print(f"Answer: {question_create.answer[:50]}...")
                print(f"Pack ID: {question_create.pack_id}")
                print(f"Topic: {question_create.pack_topics_item}")
                print(f"Difficulty: {question_create.difficulty_current}")
            
            # Create the question in the database
            return await self.question_repository.create(obj_in=question_create)
            
        except Exception as e:
            logger.error(f"Error creating question: {str(e)}")
            if self.debug_enabled:
                print(f"Error creating question: {str(e)}")
                print(traceback.format_exc())
            return None
    
    async def get_questions_by_pack_id(self, pack_id: str) -> List[Question]:
        """
        Retrieve all questions for a specific pack.
        
        Args:
            pack_id: ID of the pack
            
        Returns:
            List of Question objects
        """
        # Ensure pack_id is a valid UUID string
        pack_id = ensure_uuid(pack_id)
        
        # Use the repository to get questions
        return await self.question_repository.get_by_pack_id(pack_id)
    
    async def get_questions_by_topic(self, pack_id: str, topic: str) -> List[Question]:
        """
        Retrieve questions for a specific pack filtered by topic.
        
        Args:
            pack_id: ID of the pack
            topic: Topic to filter by
            
        Returns:
            List of Question objects
        """
        # Ensure pack_id is a valid UUID string
        pack_id = ensure_uuid(pack_id)
        
        # Get all questions for the pack
        all_questions = await self.question_repository.get_by_pack_id(pack_id)
        
        # Filter by topic
        return [q for q in all_questions if q.pack_topics_item == topic]
    
    async def update_question_statistics(
        self,
        question_id: str,
        correct: bool
    ) -> Optional[Question]:
        """
        Update question statistics based on user answer.
        
        Args:
            question_id: ID of the question
            correct: Whether the user answered correctly
            
        Returns:
            Updated Question object or None if update failed
        """
        # Ensure question_id is a valid UUID string
        question_id = ensure_uuid(question_id)
        
        # Get the question
        question = await self.question_repository.get_by_id(question_id)
        if not question:
            return None
        
        # Recalculate correct answer rate
        # This is a simple weighted average approach
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
    
    async def generate_incorrect_answers_for_questions(
        self,
        questions: List[Question],
        num_incorrect_answers: int = 3,
        debug_mode: bool = False
    ) -> List[Tuple[Question, List[str]]]:
        """
        Generate incorrect answers for questions.
        
        Args:
            questions: List of Question objects
            num_incorrect_answers: Number of incorrect answers to generate per question
            debug_mode: Enable verbose debug output
            
        Returns:
            List of tuples containing (question, incorrect_answers_list)
        """
        self.debug_enabled = debug_mode
        
        if not questions:
            return []
        
        if self.debug_enabled:
            print(f"\n=== Generating Incorrect Answers for {len(questions)} Questions ===")
        
        # Use the incorrect answer generator to create plausible but incorrect answers
        generation_results = await self.incorrect_answer_generator.generate_incorrect_answers(
            questions=questions,
            num_incorrect_answers=num_incorrect_answers,
            debug_mode=debug_mode
        )
        
        # Map results to questions
        results = []
        question_map = {q.id: q for q in questions}
        
        for question_id, incorrect_answers in generation_results:
            if question_id in question_map:
                results.append((question_map[question_id], incorrect_answers))
        
        return results
    
    async def _get_incorrect_answers_repository(self):
        """
        Get the incorrect answers repository instance.
        
        Returns:
            IncorrectAnswersRepository instance or None if not available
        """
        try:
            # Import here to avoid circular imports
            from ..repositories.incorrect_answers_repository import IncorrectAnswersRepository
            from ..config.supabase_client import init_supabase_client
            
            # Get a Supabase client
            supabase = await init_supabase_client()
            
            # Create the repository
            return IncorrectAnswersRepository(supabase)
        except Exception as e:
            logger.error(f"Error creating incorrect answers repository: {str(e)}")
            return None