from typing import List, Dict, Any, Optional
import concurrent.futures
from models.question import Question
from models.answer import Answer
from models.complete_question import CompleteQuestion
from repositories.question_repository import QuestionRepository
from utils.question_generator.generator import QuestionGenerator
from utils.question_generator.answer_generator import AnswerGenerator
from utils.question_generator.deduplicator import Deduplicator
from config.llm_config import LLMConfigFactory
import asyncio

class QuestionService:
    """
    Service for managing trivia questions
    
    This orchestrates all operations related to questions, including:
    - Generation
    - Storage
    - Retrieval
    - Game mechanics
    """
    def __init__(
        self, 
        question_repository: QuestionRepository,
        question_generator: Optional[QuestionGenerator] = None,
        answer_generator: Optional[AnswerGenerator] = None,
        deduplicator: Optional[Deduplicator] = None
    ):
        """
        Initialize question service with necessary components
        
        Args:
            question_repository (QuestionRepository): Repository for data access
            question_generator (QuestionGenerator, optional): Custom question generator
            answer_generator (AnswerGenerator, optional): Custom answer generator
            deduplicator (Deduplicator, optional): Custom deduplicator
        """
        self.repository = question_repository
        
        # Create default generators with appropriate configs if not provided
        if question_generator is None:
            # Use the default config based on environment variable
            question_config = LLMConfigFactory.create_default()
            self.generator = QuestionGenerator(question_config)
        else:
            self.generator = question_generator
            
        if answer_generator is None:
            # Use the default config based on environment variable
            answer_config = LLMConfigFactory.create_default()
            self.answer_generator = AnswerGenerator(answer_config)
        else:
            self.answer_generator = answer_generator
            
        self.deduplicator = deduplicator or Deduplicator()
        
        # Standard difficulty levels (5 tiers)
        self.difficulty_levels = ["Easy", "Medium", "Hard", "Expert", "Master"]
    
    async def generate_and_save_questions(
        self, 
        category: str, 
        count: int = 10,
        deduplicate: bool = True,
        difficulty: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[Question]:
        """
        Generate questions for a category and save them
        
        Args:
            category (str): Question category
            count (int): Number of questions to generate
            deduplicate (bool): Whether to deduplicate questions
            difficulty (str, optional): Specific difficulty level
            user_id (str, optional): user_id who created the questions
            
        Returns:
            List[Question]: Generated and saved questions
        """
        # Generate questions with specific difficulty
        questions = self.generator.generate_questions(category, count, difficulty)
        
        # Set user_id for all questions
        if user_id:
            for question in questions:
                question.user_id = user_id
        
        # Deduplicate if requested
        if deduplicate:
            questions = self.deduplicator.remove_duplicates(questions)
        
        # Save to database
        saved_questions = await self.repository.bulk_create(questions)
        
        return saved_questions
    
    async def generate_answers_for_questions(
        self,
        questions: List[Question],
        category: str,
        batch_size: int = 50
    ) -> List[Answer]:
        """
        Generate and save answers for questions
        
        Args:
            questions (List[Question]): Questions to generate answers for
            category (str): Category for context
            batch_size (int): Processing batch size
            
        Returns:
            List[Answer]: Generated answers
        """
        # Generate answers
        answers = self.answer_generator.generate_answers(
            questions=questions,
            category=category,
            batch_size=batch_size
        )
        
        # Save answers
        saved_answers = await self.repository.bulk_save_answers(answers)
        
        return saved_answers
    
    async def create_complete_question_set(
        self,
        category: str,
        count: int = 10,
        deduplicate: bool = True,
        batch_size: int = 50,
        difficulty: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[CompleteQuestion]:
        """
        Complete end-to-end pipeline: generate questions and answers
        
        Args:
            category (str): Question category
            count (int): Number of questions
            deduplicate (bool): Whether to deduplicate
            batch_size (int): Processing batch size
            difficulty (Optional[str]): Single difficulty level
            user_id (Optional[str]): user_id who created the questions
            
        Returns:
            List[CompleteQuestion]: Complete questions with answers
        """
        # Default to Medium difficulty if none specified
        if not difficulty:
            difficulty = "Medium"
        
        # Verify the difficulty is valid
        if difficulty not in self.difficulty_levels:
            difficulty = "Medium"  # Default to Medium if not valid
        
        # Print for debugging
        print(f"Generating {count} '{category}' questions with '{difficulty}' difficulty...")
        
        try:
            # Generate questions for this difficulty
            questions = await self.generate_and_save_questions(
                category=category,
                count=count,
                deduplicate=deduplicate,
                difficulty=difficulty,
                user_id=user_id
            )
        except Exception as exc:
            print(f"Generation for {difficulty} generated an exception: {exc}")
            raise
        
        # Generate and save answers for all questions
        answers = await self.generate_answers_for_questions(
            questions=questions,
            category=category,
            batch_size=batch_size
        )
        
        # Create complete questions from questions and answers
        complete_questions = []
        answer_map = {a.question_id: a for a in answers}
        
        for question in questions:
            if question.id in answer_map:
                complete_question = CompleteQuestion(
                    question=question,
                    answer=answer_map[question.id]
                )
                complete_questions.append(complete_question)
        
        return complete_questions
    
    async def get_questions_by_category(
        self,
        category: str,
        limit: int = 50
    ) -> List[Question]:
        """
        Retrieve questions by category
        
        Args:
            category (str): Category to filter by
            limit (int): Maximum results
            
        Returns:
            List[Question]: Matching questions
        """
        return await self.repository.find_by_category(category, limit)
    
    async def get_random_game_questions(
        self,
        categories=None,
        count: int = 10
    ) -> List[CompleteQuestion]:
        """
        Get random questions for a game
        
        Args:
            categories (List[str], optional): Categories to include
            count (int): Number of questions
            
        Returns:
            List[CompleteQuestion]: Random questions with answers
        """
        return await self.repository.get_random_game_questions(categories, count)
    
    async def get_complete_question(
        self,
        question_id: str
    ) -> Optional[CompleteQuestion]:
        """
        Get a complete question with its answer
        
        Args:
            question_id (str): Question ID
            
        Returns:
            Optional[CompleteQuestion]: Complete question if found
        """
        return await self.repository.get_complete_question(question_id)