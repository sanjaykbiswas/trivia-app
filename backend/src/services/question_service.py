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
            # For questions, we might want a more powerful model
            question_config = LLMConfigFactory.create_anthropic("claude-3-7-sonnet-20250219")
            self.generator = QuestionGenerator(question_config)
        else:
            self.generator = question_generator
            
        if answer_generator is None:
            # For answers, we might want a faster model
            answer_config = LLMConfigFactory.create_openai("gpt-3.5-turbo")
            self.answer_generator = AnswerGenerator(answer_config)
        else:
            self.answer_generator = answer_generator
            
        self.deduplicator = deduplicator or Deduplicator()
        
        # Standard difficulty levels (5 tiers)
        self.difficulty_levels = ["Easy", "Medium", "Hard", "Expert", "Master"]
    
    def generate_and_save_questions(
        self, 
        category: str, 
        count: int = 10,
        deduplicate: bool = True,
        difficulty: Optional[str] = None,
        user: Optional[str] = None
    ) -> List[Question]:
        """
        Generate questions for a category and save them
        
        Args:
            category (str): Question category
            count (int): Number of questions to generate
            deduplicate (bool): Whether to deduplicate questions
            difficulty (str, optional): Specific difficulty level
            user (str, optional): User who created the questions
            
        Returns:
            List[Question]: Generated and saved questions
        """
        # Generate questions
        if difficulty:
            # Generate questions for a specific difficulty
            questions = self.generator.generate_questions(category, count, difficulty)
        else:
            # Use the new multi-difficulty generation method
            questions = self.generate_questions_across_difficulties(category, count)
        
        # Set user for all questions
        if user:
            for question in questions:
                question.user = user
        
        # Deduplicate if requested
        if deduplicate:
            questions = self.deduplicator.remove_duplicates(questions)
        
        # Save to database
        saved_questions = self.repository.bulk_create(questions)
        
        return saved_questions
    
    def generate_questions_across_difficulties(
        self,
        category: str,
        count: int = 10,
        difficulties: List[str] = None,
        user: Optional[str] = None
    ) -> List[Question]:
        """
        Generate questions across multiple difficulty tiers concurrently
        
        Args:
            category (str): Question category
            count (int): Total number of questions to generate
            difficulties (List[str], optional): List of difficulties to include
                                               Defaults to all five difficulty levels
            user (str, optional): User who created the questions
            
        Returns:
            List[Question]: Generated questions across all difficulty tiers
        """
        # Default to all five difficulty levels if not specified
        if difficulties is None:
            difficulties = self.difficulty_levels
        else:
            # Filter to only include valid difficulty levels
            difficulties = [d for d in difficulties if d in self.difficulty_levels]
            if not difficulties:
                difficulties = ["Medium"]  # Default to Medium if none are valid
        
        # Calculate questions per difficulty, distributing evenly
        questions_per_difficulty = max(1, count // len(difficulties))
        remainder = count % len(difficulties)
        
        # Distribute the remainder among the first few difficulties
        counts = [questions_per_difficulty + (1 if i < remainder else 0) for i in range(len(difficulties))]
        
        # Generate questions for each difficulty tier concurrently
        all_questions = []
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_difficulty = {
                executor.submit(
                    self.generator.generate_questions, 
                    category, 
                    counts[i], 
                    difficulty
                ): difficulty 
                for i, difficulty in enumerate(difficulties)
            }
            
            for future in concurrent.futures.as_completed(future_to_difficulty):
                try:
                    questions = future.result()

                    # Set user for all questions
                    if user:
                        for question in questions:
                            question.user = user
                    
                    all_questions.extend(questions)
                except Exception as exc:
                    difficulty = future_to_difficulty[future]
                    print(f"Generation for {difficulty} generated an exception: {exc}")
        
        return all_questions
    
    def generate_answers_for_questions(
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
        saved_answers = self.repository.bulk_save_answers(answers)
        
        return saved_answers
    
    def create_complete_question_set(
        self,
        category: str,
        count: int = 10,
        deduplicate: bool = True,
        batch_size: int = 50,
        difficulties: List[str] = None,
        user: Optional[str] = None
    ) -> List[CompleteQuestion]:
        """
        Complete end-to-end pipeline: generate questions and answers
        
        Args:
            category (str): Question category
            count (int): Number of questions
            deduplicate (bool): Whether to deduplicate
            batch_size (int): Processing batch size
            difficulties (List[str], optional): List of difficulties to include
            user (str, optional): User who created the questions
            
        Returns:
            List[CompleteQuestion]: Complete questions with answers
        """
        # Generate and save questions across difficulty tiers
        questions = self.generate_and_save_questions(
            category=category,
            count=count,
            deduplicate=deduplicate,
            difficulty=None,  # Use multi-difficulty generation
            user=user
        )
        
        # Generate and save answers
        answers = self.generate_answers_for_questions(
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
    
    def get_questions_by_category(
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
        return self.repository.find_by_category(category, limit)
    
    def get_random_game_questions(
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
        return self.repository.get_random_game_questions(categories, count)
    
    def get_complete_question(
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
        return self.repository.get_complete_question(question_id)