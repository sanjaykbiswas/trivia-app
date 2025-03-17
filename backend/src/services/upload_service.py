from typing import List, Dict, Any, Optional
from models.question import Question
from models.answer import Answer
from models.complete_question import CompleteQuestion
from config.environment import Environment
from utils.supabase_actions import SupabaseActions

class UploadService:
    """
    Service for handling uploads to the Supabase database
    
    This service orchestrates the upload of trivia questions and answers,
    ensuring proper user creation when necessary.
    """
    def __init__(self, supabase_client):
        """
        Initialize the upload service
        
        Args:
            supabase_client: Initialized Supabase client
        """
        self.supabase_actions = SupabaseActions(supabase_client)
    
    async def upload_complete_question(
        self, 
        question_content: str,
        category: str,
        correct_answer: str,
        incorrect_answers: List[str],
        difficulty: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> CompleteQuestion:
        """
        Create and upload a complete question with answer
        
        Args:
            question_content (str): The question text
            category (str): Category of the question
            correct_answer (str): The correct answer
            incorrect_answers (List[str]): List of incorrect answers
            difficulty (Optional[str]): Difficulty level
            user_id (Optional[str]): User ID (system ID used if not provided)
            
        Returns:
            CompleteQuestion: The saved complete question
        """
        # Create question object
        question = Question(
            content=question_content,
            category=category,
            difficulty=difficulty,
            user_id=user_id or "00000000-0000-0000-0000-000000000000"
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
    
    async def bulk_upload_complete_questions(
        self,
        complete_questions: List[Dict[str, Any]]
    ) -> List[CompleteQuestion]:
        """
        Upload multiple complete questions in bulk
        
        Args:
            complete_questions (List[Dict]): List of question data dictionaries
                Each should have: content, category, correct_answer, incorrect_answers
                Optional: difficulty, user_id
                
        Returns:
            List[CompleteQuestion]: List of saved complete questions
        """
        questions = []
        answers = []
        
        # Prepare question and answer objects
        for q_data in complete_questions:
            user_id = q_data.get("user_id", "00000000-0000-0000-0000-000000000000")
            
            # Create question object
            question = Question(
                content=q_data["content"],
                category=q_data["category"],
                difficulty=q_data.get("difficulty"),
                user_id=user_id
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