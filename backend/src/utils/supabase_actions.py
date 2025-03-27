from typing import Optional, Dict, Any, List
import logging
from models.question import Question
from models.answer import Answer
from models.user import User, AuthProvider
from config.environment import Environment
from datetime import datetime

# Configure logger
logger = logging.getLogger(__name__)

class SupabaseActions:
    """
    Utility class for database upload actions to Supabase
    
    Provides methods to save questions and answers
    """
    def __init__(self, supabase_client):
        """
        Initialize with Supabase client
        
        Args:
            supabase_client: Initialized Supabase client
        """
        self.client = supabase_client
        self.questions_table = "questions"
        self.answers_table = "answers"
        self.users_table = "users"
    
    async def save_question(self, question: Question) -> Question:
        """
        Save a question to Supabase
        
        Args:
            question (Question): Question object to save
            
        Returns:
            Question: Saved question with ID
        """
        logger.info(f"Saving question: {question.content[:30]}...")
        
        # Save question
        response = (
            self.client
            .table(self.questions_table)
            .insert(question.to_dict())
            .execute()
        )
        
        if response.data:
            question.id = response.data[0]["id"]
            logger.info(f"Question saved with ID: {question.id}")
        else:
            logger.error("Failed to save question: No data returned from Supabase")
        
        return question
    
    async def save_answer(self, answer: Answer) -> Answer:
        """
        Save an answer to Supabase
        
        Args:
            answer (Answer): Answer object to save
            
        Returns:
            Answer: Saved answer with ID
        """
        logger.info(f"Saving answer for question ID: {answer.question_id}")
        
        response = (
            self.client
            .table(self.answers_table)
            .insert(answer.to_dict())
            .execute()
        )
        
        if response.data:
            answer.id = response.data[0]["id"]
            logger.info(f"Answer saved with ID: {answer.id}")
        else:
            logger.error("Failed to save answer: No data returned from Supabase")
        
        return answer
    
    async def save_question_and_answer(self, question: Question, answer: Answer) -> Dict[str, Any]:
        """
        Save both question and answer objects to Supabase
        
        Args:
            question (Question): Question object to save
            answer (Answer): Answer object to save (without question_id)
            
        Returns:
            Dict[str, Any]: Dictionary with saved question and answer objects
        """
        # Save question first
        saved_question = await self.save_question(question)
        
        # Set question_id on answer
        answer.question_id = saved_question.id
        
        # Save answer
        saved_answer = await self.save_answer(answer)
        
        return {
            "question": saved_question,
            "answer": saved_answer
        }
    
    async def bulk_save_questions_and_answers(
        self, 
        questions: List[Question], 
        answers: List[Answer]
    ) -> List[Dict[str, Any]]:
        """
        Save multiple question and answer pairs to Supabase
        
        Args:
            questions (List[Question]): List of question objects
            answers (List[Answer]): List of answer objects (without question_ids)
            
        Returns:
            List[Dict[str, Any]]: List of dictionaries with saved question and answer objects
        """
        if len(questions) != len(answers):
            raise ValueError("Number of questions and answers must match")
        
        results = []
        for i, (question, answer) in enumerate(zip(questions, answers)):
            result = await self.save_question_and_answer(question, answer)
            results.append(result)
        
        return results
    
    async def ensure_user_exists(self, user_id: str, username: Optional[str] = None) -> Dict[str, Any]:
        """
        Ensure a user exists in the users table, creating if necessary
        
        Args:
            user_id (str): User ID
            username (str, optional): Username for new user
            
        Returns:
            Dict[str, Any]: User data
        """
        logger.info(f"Ensuring user exists: {user_id}")
        
        # Check if user exists
        response = (
            self.client
            .table(self.users_table)
            .select("*")
            .eq("id", user_id)
            .execute()
        )
        
        # If user exists, return user data
        if response.data and len(response.data) > 0:
            logger.info(f"User {user_id} already exists")
            return response.data[0]
        
        # User doesn't exist, create new user
        logger.info(f"Creating new user: {user_id}")
        user_data = {
            "id": user_id,
            "username": username,
            "created_at": datetime.now().isoformat()
        }
        
        create_response = (
            self.client
            .table(self.users_table)
            .insert(user_data)
            .execute()
        )
        
        if create_response.data and len(create_response.data) > 0:
            logger.info(f"User {user_id} created successfully")
            return create_response.data[0]
        else:
            logger.error(f"Failed to create user with ID: {user_id}")
            raise ValueError(f"Failed to create user with ID: {user_id}")
    
    async def create_temporary_user(self, username: str) -> Dict[str, Any]:
        """
        Create a temporary user with just a username
        
        Args:
            username (str): User's display name
            
        Returns:
            Dict[str, Any]: User data with generated ID
        """
        logger.info(f"Creating temporary user with username: {username}")
        
        # Create user data
        user_data = {
            "username": username,
            "is_temporary": True,
            "auth_provider": "none",
            "created_at": datetime.now().isoformat()
        }
        
        # Insert into users table
        create_response = (
            self.client
            .table(self.users_table)
            .insert(user_data)
            .execute()
        )
        
        if create_response.data and len(create_response.data) > 0:
            logger.info(f"Temporary user created with ID: {create_response.data[0]['id']}")
            return create_response.data[0]
        else:
            logger.error(f"Failed to create temporary user")
            raise ValueError(f"Failed to create temporary user")

    async def link_user_identity(self, temp_user_id: str, auth_id: str, auth_provider: str, email: Optional[str] = None, avatar_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Link a temporary user to an authenticated identity
        
        Args:
            temp_user_id (str): Temporary user ID
            auth_id (str): Authentication provider's user ID
            auth_provider (str): Authentication provider name (email, google, apple)
            email (str, optional): User's email
            avatar_url (str, optional): User's avatar URL
            
        Returns:
            Dict[str, Any]: Updated user data
        """
        logger.info(f"Linking user {temp_user_id} to auth identity {auth_id} from {auth_provider}")
        
        # First, check if the user exists
        user_response = (
            self.client
            .table(self.users_table)
            .select("*")
            .eq("id", temp_user_id)
            .execute()
        )
        
        if not user_response.data or len(user_response.data) == 0:
            logger.error(f"User {temp_user_id} not found")
            raise ValueError(f"User {temp_user_id} not found")
        
        # Check if this is a temporary user
        user_data = user_response.data[0]
        if not user_data.get("is_temporary", False):
            logger.warning(f"User {temp_user_id} is already linked to an auth provider")
            return user_data  # Return existing data
        
        # Update user with auth information
        update_data = {
            "is_temporary": False,
            "auth_provider": auth_provider,
            "auth_id": auth_id
        }
        
        # Add optional fields if provided
        if email:
            update_data["email"] = email
        
        if avatar_url:
            update_data["avatar_url"] = avatar_url
        
        # Update the user record
        update_response = (
            self.client
            .table(self.users_table)
            .update(update_data)
            .eq("id", temp_user_id)
            .execute()
        )
        
        if update_response.data and len(update_response.data) > 0:
            logger.info(f"User {temp_user_id} successfully linked to auth identity")
            return update_response.data[0]
        else:
            logger.error(f"Failed to update user {temp_user_id}")
            raise ValueError(f"Failed to update user {temp_user_id}")

    async def find_user_by_auth(self, auth_id: str, auth_provider: str) -> Optional[Dict[str, Any]]:
        """
        Find a user by authentication credentials
        
        Args:
            auth_id (str): Authentication provider's user ID
            auth_provider (str): Authentication provider name
            
        Returns:
            Optional[Dict[str, Any]]: User data if found
        """
        response = (
            self.client
            .table(self.users_table)
            .select("*")
            .eq("auth_id", auth_id)
            .eq("auth_provider", auth_provider)
            .execute()
        )
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        
        return None