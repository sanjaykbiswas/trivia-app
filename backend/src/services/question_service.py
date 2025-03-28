from typing import List, Dict, Any, Optional
import asyncio
from models.question import Question
from models.answer import Answer
from models.complete_question import CompleteQuestion
from repositories.question_repository import QuestionRepository
from repositories.category_repository import CategoryRepository
from utils.question_generator.generator import QuestionGenerator
from utils.question_generator.answer_generator import AnswerGenerator
from utils.question_generator.deduplicator import Deduplicator
from config.llm_config import LLMConfigFactory
import logging

# Configure logger
logger = logging.getLogger(__name__)

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
        deduplicator: Optional[Deduplicator] = None,
        category_repository: Optional[CategoryRepository] = None
    ):
        """
        Initialize question service with necessary components
        
        Args:
            question_repository (QuestionRepository): Repository for data access
            question_generator (QuestionGenerator, optional): Custom question generator
            answer_generator (AnswerGenerator, optional): Custom answer generator
            deduplicator (Deduplicator, optional): Custom deduplicator
            category_repository (CategoryRepository, optional): Repository for category operations
        """
        self.repository = question_repository
        self.category_repository = category_repository
        
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
    
    async def get_category_repository(self):
        """
        Lazy initialization of category repository if not provided
        
        Returns:
            CategoryRepository: Repository for category operations
        """
        if not self.category_repository:
            # Use the repository reference from the question repository if available
            if hasattr(self.repository, 'category_repository') and self.repository.category_repository:
                self.category_repository = self.repository.category_repository
            else:
                # Create a new repository instance if needed
                supabase_client = getattr(self.repository, 'client', None)
                if supabase_client:
                    from repositories.category_repository import CategoryRepository
                    self.category_repository = CategoryRepository(supabase_client)
                else:
                    logger.error("Cannot initialize category repository - no Supabase client available")
        return self.category_repository

    async def resolve_category_id(self, category_name: str) -> str:
        """
        Resolve a category ID from name, creating if necessary
        
        Args:
            category_name (str): Category name to resolve
            
        Returns:
            str: Category ID
        """
        if not category_name:
            return None
            
        # Look up or create the category
        try:
            category_repo = await self.get_category_repository()
            if not category_repo:
                logger.warning(f"No category repository available to resolve '{category_name}'")
                return None
                
            category = await category_repo.get_or_create_by_name(category_name)
            return category.id if category else None
        except Exception as e:
            logger.error(f"Error resolving category ID for name '{category_name}': {e}")
            return None
    
    async def resolve_category_name(self, category_id: str) -> str:
        """
        Resolve a category name from ID
        
        Args:
            category_id (str): Category ID to resolve
            
        Returns:
            str: Category name or None if not found
        """
        if not category_id:
            return None
            
        # Check if it's already a name (not a UUID)
        if not isinstance(category_id, str) or '-' not in category_id:
            return category_id
            
        try:
            category_repo = await self.get_category_repository()
            if not category_repo:
                logger.warning(f"No category repository available to resolve category ID '{category_id}'")
                return category_id
                
            category = await category_repo.get_by_id(category_id)
            return category.name if category else category_id
        except Exception as e:
            logger.error(f"Error resolving category name for ID '{category_id}': {e}")
            return category_id
    
    async def generate_and_save_questions(
        self, 
        category: str, 
        count: int = 10,
        deduplicate: bool = True,
        difficulty: Optional[str] = None
    ) -> List[Question]:
        """
        Generate questions for a category and save them
        
        Args:
            category (str): Question category (name or ID)
            count (int): Number of questions to generate
            deduplicate (bool): Whether to deduplicate questions
            difficulty (str, optional): Specific difficulty level
            
        Returns:
            List[Question]: Generated and saved questions
        """
        # Standardize difficulty if provided
        standard_difficulty = None
        if difficulty:
            standard_difficulty = self._standardize_difficulty(difficulty)
            
        # Resolve category name if needed
        category_name = await self.resolve_category_name(category)
        
        # Get category ID
        category_id = None
        if '-' in category:  # Looks like UUID
            category_id = category
        else:
            category_id = await self.resolve_category_id(category)
        
        if not category_id:
            logger.warning(f"Could not resolve category ID for '{category}', using name only")
        
        # Generate questions with specific difficulty using async method
        try:
            # Generate questions with category name for better LLM context
            raw_questions = await self.generator.generate_questions_async(
                category=category_name, 
                count=count, 
                difficulty=standard_difficulty
            )
            
            # Update questions with category ID before saving
            for question in raw_questions:
                question.category_id = category_id
                question.category_name = category_name
                
            # Deduplicate if requested
            if deduplicate:
                raw_questions = self.deduplicator.remove_duplicates(raw_questions)
            
            # Initialize modified_difficulty with the same value as difficulty
            for question in raw_questions:
                question.modified_difficulty = question.difficulty
            
            # Save to database
            saved_questions = await self.repository.bulk_create(raw_questions)
            
            return saved_questions
            
        except Exception as e:
            logger.error(f"Error in question generation: {e}")
            raise
    
    # The rest of the methods in the service class remain similar
    # but need updates to handle category_id and category_name appropriately
    
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
        # Resolve category name if needed for better context
        category_name = await self.resolve_category_name(category)
        
        # Check if we already have an asyncio event loop running
        try:
            loop = asyncio.get_running_loop()
            # We're already in an event loop
            try:
                # Try using the async version if available
                if hasattr(self.answer_generator, 'generate_answers_async'):
                    answers = await self.answer_generator.generate_answers_async(
                        questions=questions,
                        category=category_name,
                        batch_size=batch_size
                    )
                else:
                    # Use the synchronous version which should handle this case
                    answers = self.answer_generator.generate_answers(
                        questions=questions,
                        category=category_name,
                        batch_size=batch_size
                    )
            except RuntimeError as e:
                # If we get an event loop error, use the sync version
                logger.warning(f"Using synchronous answer generation due to: {e}")
                answers = self.answer_generator.generate_answers(
                    questions=questions,
                    category=category_name,
                    batch_size=batch_size
                )
        except RuntimeError:
            # No event loop is running, call the regular generate_answers
            answers = self.answer_generator.generate_answers(
                questions=questions,
                category=category_name,
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
        difficulty: Optional[str] = None
    ) -> List[CompleteQuestion]:
        """
        Complete end-to-end pipeline: generate questions and answers
        
        Args:
            category (str): Question category (name or ID)
            count (int): Number of questions
            deduplicate (bool): Whether to deduplicate
            batch_size (int): Processing batch size
            difficulty (Optional[str]): Single difficulty level
            
        Returns:
            List[CompleteQuestion]: Complete questions with answers
        """
        # Default to Medium difficulty if none specified
        if not difficulty:
            difficulty = "Medium"
        
        # Verify the difficulty is valid
        if difficulty not in self.difficulty_levels:
            difficulty = "Medium"  # Default to Medium if not valid
        
        # Resolve category name for logging
        category_name = await self.resolve_category_name(category)
        
        # Print for debugging
        logger.info(f"Generating {count} '{category_name}' questions with '{difficulty}' difficulty...")
        
        try:
            # Generate questions for this difficulty
            questions = await self.generate_and_save_questions(
                category=category,
                count=count,
                deduplicate=deduplicate,
                difficulty=difficulty
            )
        except Exception as exc:
            logger.error(f"Generation for {difficulty} generated an exception: {exc}")
            raise
        
        # Generate and save answers for all questions
        answers = await self.generate_answers_for_questions(
            questions=questions,
            category=category_name,
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

    async def create_multi_difficulty_question_set(
        self,
        category: str,
        difficulty_counts: Dict[str, int],
        deduplicate: bool = True,
        batch_size: int = 50
    ) -> Dict[str, List[CompleteQuestion]]:
        """
        Generate complete question sets with different difficulties concurrently
        
        Args:
            category (str): Question category (name or ID)
            difficulty_counts (Dict[str, int]): Dictionary mapping difficulty levels to counts
                Example: {"Easy": 5, "Hard": 10, "Master": 3}
            deduplicate (bool): Whether to deduplicate questions within each difficulty
            batch_size (int): Processing batch size for answer generation
            
        Returns:
            Dict[str, List[CompleteQuestion]]: Dictionary mapping difficulty levels to complete questions
        """
        # Validate difficulty levels
        valid_difficulties = {}
        for difficulty, count in difficulty_counts.items():
            if difficulty in self.difficulty_levels and count > 0:
                valid_difficulties[difficulty] = min(count, 100)  # Limit to 100 questions per difficulty
        
        if not valid_difficulties:
            raise ValueError(f"No valid difficulties specified. Valid options are: {self.difficulty_levels}")
        
        # Resolve category name
        category_name = await self.resolve_category_name(category)
        
        # Pre-generate category guidelines and difficulty contexts for all difficulties once
        logger.info(f"Pre-generating shared guidelines for category: '{category_name}'")
        
        # Use the generator's helpers to pre-generate category guidelines
        category_guidelines = await asyncio.to_thread(
            self.generator.category_helper.generate_category_guidelines,
            category_name
        )
        
        # Pre-generate all difficulty tiers at once
        difficulty_tiers = await asyncio.to_thread(
            self.generator.difficulty_helper.generate_difficulty_guidelines,
            category_name
        )
        
        # Cache the generated guidelines in the generator's caches
        category_key = category_name.lower().strip()
        self.generator._category_guidelines_cache[category_key] = category_guidelines
        
        # Cache each difficulty context
        for difficulty in valid_difficulties.keys():
            standard_difficulty = self._standardize_difficulty(difficulty)
            difficulty_context = self.generator.difficulty_helper.get_difficulty_by_tier(
                difficulty_tiers, 
                standard_difficulty
            )
            if difficulty_context:
                difficulty_context = f"\nDifficulty Level:\n{difficulty_context}"
                
            # Cache the context
            difficulty_cache_key = f"{category_key}:{standard_difficulty.lower().strip()}"
            self.generator._difficulty_context_cache[difficulty_cache_key] = difficulty_context
        
        # Now create tasks for generating questions for each difficulty concurrently
        question_tasks = {}
        for difficulty, count in valid_difficulties.items():
            # Create a task for each difficulty
            task = asyncio.create_task(
                self.generate_and_save_questions(
                    category=category,
                    count=count,
                    deduplicate=deduplicate,
                    difficulty=difficulty
                )
            )
            question_tasks[difficulty] = task
        
        # Wait for all question generation tasks to complete
        questions_by_difficulty = {}
        for difficulty, task in question_tasks.items():
            try:
                questions_by_difficulty[difficulty] = await task
            except Exception as e:
                logger.error(f"Error generating questions for {difficulty} difficulty: {e}")
                questions_by_difficulty[difficulty] = []
        
        # Flatten all questions for answer generation
        all_questions = []
        for questions in questions_by_difficulty.values():
            all_questions.extend(questions)
        
        # If no questions were generated, return empty result
        if not all_questions:
            return {difficulty: [] for difficulty in valid_difficulties}
        
        # Generate answers for all questions at once
        answers = await self.generate_answers_for_questions(
            questions=all_questions,
            category=category_name,
            batch_size=batch_size
        )
        
        # Create a mapping of question_id to answer
        answer_map = {a.question_id: a for a in answers}
        
        # Organize complete questions by difficulty
        result = {}
        for difficulty, questions in questions_by_difficulty.items():
            complete_questions = []
            for question in questions:
                if question.id in answer_map:
                    complete_question = CompleteQuestion(
                        question=question,
                        answer=answer_map[question.id]
                    )
                    complete_questions.append(complete_question)
            result[difficulty] = complete_questions
        
        return result
    
    # Helper methods
    def _standardize_difficulty(self, difficulty):
        """
        Convert difficulty input to standard format
        
        Args:
            difficulty: Input difficulty (str or int)
            
        Returns:
            str: Standardized difficulty level
        """
        # Convert to standard difficulty format
        if isinstance(difficulty, int) and 1 <= difficulty <= 5:
            return self.difficulty_levels[difficulty-1]
        elif isinstance(difficulty, str) and difficulty in self.difficulty_levels:
            return difficulty
        elif isinstance(difficulty, str):
            # Try to match difficulty string to standard level
            for level in self.difficulty_levels:
                if level.lower() in difficulty.lower():
                    return level
            
        # Default to Medium if not matched
        return "Medium"
    
    # Query methods
    async def get_questions_by_category(
        self,
        category: str,
        limit: int = 50
    ) -> List[Question]:
        """
        Retrieve questions by category
        
        Args:
            category (str): Category ID or name to filter by
            limit (int): Maximum results
            
        Returns:
            List[Question]: Matching questions
        """
        # Handle both category IDs and names
        if '-' in category:  # Looks like UUID
            # Use category ID directly
            return await self.repository.find_by_category(category, limit)
        else:
            # Look up by category name
            return await self.repository.find_by_category_name(category, limit)
    
    async def get_random_game_questions(
        self,
        categories=None,
        count: int = 10
    ) -> List[CompleteQuestion]:
        """
        Get random questions for a game
        
        Args:
            categories (List[str], optional): Category IDs or names to include
            count (int): Number of questions
            
        Returns:
            List[CompleteQuestion]: Random questions with answers
        """
        # If category names were provided, resolve to IDs
        if categories and any(cat for cat in categories if '-' not in cat):
            resolved_categories = []
            for cat in categories:
                if '-' not in cat:  # Not a UUID, needs resolution
                    cat_id = await self.resolve_category_id(cat)
                    if cat_id:
                        resolved_categories.append(cat_id)
                else:
                    resolved_categories.append(cat)
            categories = resolved_categories
        
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