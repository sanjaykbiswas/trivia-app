from typing import Optional, Dict, Any, List
from models.question import Question
from models.answer import Answer
from config.environment import Environment
from datetime import datetime

class SupabaseActions:
    """
    Utility class for database upload actions to Supabase
    
    Provides methods to save questions and answers, managing user creation
    when necessary
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
        Save a question to Supabase, ensuring the user exists
        
        Args:
            question (Question): Question object to save
            
        Returns:
            Question: Saved question with ID
        """
        # Ensure user exists
        await self.ensure_user_exists(question.user_id)
        
        # Save question
        response = (
            self.client
            .table(self.questions_table)
            .insert(question.to_dict())
            .execute()
        )
        
        if response.data:
            question.id = response.data[0]["id"]
        
        return question
    
    async def save_answer(self, answer: Answer) -> Answer:
        """
        Save an answer to Supabase
        
        Args:
            answer (Answer): Answer object to save
            
        Returns:
            Answer: Saved answer with ID
        """
        response = (
            self.client
            .table(self.answers_table)
            .insert(answer.to_dict())
            .execute()
        )
        
        if response.data:
            answer.id = response.data[0]["id"]
        
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
            return response.data[0]
        
        # User doesn't exist, create new user
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
            return create_response.data[0]
        else:
            raise ValueError(f"Failed to create user with ID: {user_id}")