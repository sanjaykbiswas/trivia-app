from typing import List, Dict, Any, Optional
import logging
from models.question import Question
from models.answer import Answer
from models.complete_question import CompleteQuestion
from services.service_base import ServiceBase
from utils.supabase_actions import SupabaseActions
from utils.error_handling import async_handle_errors
from utils.category_utils import CategoryUtils

# Configure logger
logger = logging.getLogger(__name__)

class RefactoredUploadService(ServiceBase):
    """
    Refactored service for handling uploads to the Supabase database
    
    This service orchestrates the upload of trivia questions and answers
    """
    def __init__(self, supabase_client, category_repository=None):
        """
        Initialize the upload service
        
        Args:
            supabase_client: Initialized Supabase client
            category_repository (optional): Repository for category operations
        """
        super().__init__(None, category_repository)
        self.supabase_actions = SupabaseActions(supabase_client)
        self.category_utils = CategoryUtils()
    
    @async_handle_errors
    async def upload_complete_question(
        self, 
        question_content: str,
        category: str,
        correct_answer: str,
        incorrect_answers: List[str],
        difficulty: Optional[str] = None,
        modified_difficulty: Optional[str] = None
    ) -> CompleteQuestion:
        """
        Create and upload a complete question with answer
        
        Args:
            question_content (str): The question text
            category (str): Category name or ID
            correct_answer (str): The correct answer
            incorrect_answers (List[str]): List of incorrect answers
            difficulty (Optional[str]): Difficulty level
            modified_difficulty (Optional[str]): Modified difficulty level
            
        Returns:
            CompleteQuestion: The saved complete question
        """
        # Determine if category is an ID or name
        category_id = None
        category_name = None
        
        if '-' in category:  # Looks like UUID
            category_id = category
            # Try to resolve the name for reference
            category_name = await self.category_utils.resolve_category_name(category_id)
        else:
            # Resolve category name to ID
            category_name = category
            category_id = await self.category_utils.get_or_create_category_id(category_name)
        
        # Create question object
        question = Question(
            content=question_content,
            category_id=category_id,
            category_name=category_name,
            difficulty=difficulty,
            modified_difficulty=modified_difficulty or difficulty  # Use difficulty if modified_difficulty not provided
        )
        
        # Create answer object (without question_id for now)
        answer = Answer(
            question_id="",  # Will be filled after question is saved
            correct_answer=correct_answer,
            incorrect_answers=incorrect_answers
        )
        
        # Save both
        result = await self.supabase_actions.save_question_and_answer(question, answer)
        
        # Return as CompleteQuestion
        return CompleteQuestion(
            question=result["question"],
            answer=result["answer"]
        )
    
    @async_handle_errors
    async def bulk_upload_complete_questions(
        self,
        complete_questions: List[Dict[str, Any]]
    ) -> List[CompleteQuestion]:
        """
        Upload multiple complete questions in bulk
        
        Args:
            complete_questions (List[Dict]): List of question data dictionaries
                Each should have: content, category, correct_answer, incorrect_answers
                Optional: difficulty, modified_difficulty
                
        Returns:
            List[CompleteQuestion]: List of saved complete questions
        """
        questions = []
        answers = []
        
        # For batching category name resolution
        category_name_to_id = {}
        
        # First pass: collect unique category names
        category_names = set()
        for q_data in complete_questions:
            category = q_data.get("category")
            if category and isinstance(category, str) and '-' not in category:
                category_names.add(category)
        
        # Batch resolve category names to IDs
        for name in category_names:
            category_id = await self.category_utils.get_or_create_category_id(name)
            if category_id:
                category_name_to_id[name] = category_id
        
        # Prepare question and answer objects
        for q_data in complete_questions:
            # Handle category resolution
            category = q_data.get("category")
            category_id = None
            category_name = None
            
            if category:
                if isinstance(category, str):
                    if '-' in category:  # Looks like UUID
                        category_id = category
                        # Try to find name if we have the repository
                        category_name = await self.category_utils.resolve_category_name(category_id)
                    else:
                        category_name = category
                        # Use cached ID if available
                        category_id = category_name_to_id.get(category_name)
                        if not category_id:
                            # Resolve individually if not in cache
                            category_id = await self.category_utils.get_or_create_category_id(category_name)
            
            # Create question object
            question = Question(
                content=q_data["content"],
                category_id=category_id,
                category_name=category_name,
                difficulty=q_data.get("difficulty"),
                modified_difficulty=q_data.get("modified_difficulty") or q_data.get("difficulty")
            )
            questions.append(question)
            
            # Create answer object (without question_id for now)
            answer = Answer(
                question_id="",  # Will be filled during saving
                correct_answer=q_data["correct_answer"],
                incorrect_answers=q_data["incorrect_answers"]
            )
            answers.append(answer)
        
        # Bulk save
        results = await self.supabase_actions.bulk_save_questions_and_answers(questions, answers)
        
        # Convert to CompleteQuestion objects
        complete_questions = []
        for result in results:
            complete_questions.append(
                CompleteQuestion(
                    question=result["question"],
                    answer=result["answer"]
                )
            )
        
        return complete_questions
    
    @async_handle_errors
    async def register_user(self, user_id: str, username: Optional[str] = None) -> Dict[str, Any]:
        """
        Register a new user or ensure existing user
        
        Args:
            user_id (str): User ID
            username (Optional[str]): Username (can be null)
            
        Returns:
            Dict[str, Any]: User data
        """
        return await self.supabase_actions.ensure_user_exists(user_id, username)