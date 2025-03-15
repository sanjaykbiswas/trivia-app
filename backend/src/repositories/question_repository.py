from typing import List, Dict, Any, Optional
import json
from models.question import Question
from models.answer import Answer
from models.complete_question import CompleteQuestion
from repositories.base_repository import BaseRepository
from config.environment import Environment

class QuestionRepository(BaseRepository[Question]):
    """
    Repository for managing trivia questions in Supabase
    """
    def __init__(self, supabase_client):
        self.client = supabase_client
        self.questions_table = "questions"
        self.answers_table = "answers"
    
    def create(self, question: Question) -> Question:
        """
        Create a single question
        
        Args:
            question (Question): Question to create
            
        Returns:
            Question: Created question with ID
        """
        response = (
            self.client
            .table(self.questions_table)
            .insert(question.to_dict())
            .execute()
        )
        
        if response.data:
            question.id = response.data[0]["id"]
        
        return question
    
    def bulk_create(self, questions: List[Question]) -> List[Question]:
        """
        Create multiple questions
        
        Args:
            questions (List[Question]): Questions to create
            
        Returns:
            List[Question]: Created questions with IDs
        """
        question_dicts = [q.to_dict() for q in questions]
        
        response = (
            self.client
            .table(self.questions_table)
            .insert(question_dicts)
            .execute()
        )
        
        # Set IDs on the original question objects
        for idx, data in enumerate(response.data):
            questions[idx].id = data["id"]
        
        return questions
    
    def get_by_id(self, id: str) -> Optional[Question]:
        """
        Get question by ID
        
        Args:
            id (str): Question ID
            
        Returns:
            Optional[Question]: Question if found
        """
        response = (
            self.client
            .table(self.questions_table)
            .select("*")
            .eq("id", id)
            .execute()
        )
        
        if response.data:
            return Question.from_dict(response.data[0])
        
        return None
    
    def find(self, filter_params: Dict[str, Any], limit: int = 100) -> List[Question]:
        """
        Find questions matching criteria
        
        Args:
            filter_params (Dict[str, Any]): Filter criteria
            limit (int): Maximum results
            
        Returns:
            List[Question]: Matching questions
        """
        query = self.client.table(self.questions_table).select("*")
        
        # Apply filters
        for key, value in filter_params.items():
            query = query.eq(key, value)
        
        response = query.limit(limit).execute()
        
        return [Question.from_dict(data) for data in response.data]
    
    def find_by_category(self, category: str, limit: int = 50) -> List[Question]:
        """
        Find questions by category
        
        Args:
            category (str): Category to filter by
            limit (int): Maximum results
            
        Returns:
            List[Question]: Matching questions
        """
        return self.find({"category": category}, limit)
    
    def update(self, id: str, data: Dict[str, Any]) -> Optional[Question]:
        """
        Update a question
        
        Args:
            id (str): Question ID
            data (Dict[str, Any]): Update data
            
        Returns:
            Optional[Question]: Updated question
        """
        response = (
            self.client
            .table(self.questions_table)
            .update(data)
            .eq("id", id)
            .execute()
        )
        
        if response.data:
            return Question.from_dict(response.data[0])
        
        return None
    
    def delete(self, id: str) -> bool:
        """
        Delete a question
        
        Args:
            id (str): Question ID
            
        Returns:
            bool: Success status
        """
        response = (
            self.client
            .table(self.questions_table)
            .delete()
            .eq("id", id)
            .execute()
        )
        
        return len(response.data) > 0
    
    def save_answer(self, answer: Answer) -> Answer:
        """
        Save an answer
        
        Args:
            answer (Answer): Answer to save
            
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
    
    def bulk_save_answers(self, answers: List[Answer]) -> List[Answer]:
        """
        Save multiple answers
        
        Args:
            answers (List[Answer]): Answers to save
            
        Returns:
            List[Answer]: Saved answers with IDs
        """
        answer_dicts = [a.to_dict() for a in answers]
        
        response = (
            self.client
            .table(self.answers_table)
            .insert(answer_dicts)
            .execute()
        )
        
        # Set IDs on the original answer objects
        for idx, data in enumerate(response.data):
            answers[idx].id = data["id"]
        
        return answers
    
    def get_complete_question(self, question_id: str) -> Optional[CompleteQuestion]:
        """
        Get a question with its answer
        
        Args:
            question_id (str): Question ID
            
        Returns:
            Optional[CompleteQuestion]: Complete question if found
        """
        # Get question
        question = self.get_by_id(question_id)
        if not question:
            return None
        
        # Get answer
        response = (
            self.client
            .table(self.answers_table)
            .select("*")
            .eq("question_id", question_id)
            .execute()
        )
        
        if not response.data:
            return None
        
        answer = Answer.from_dict(response.data[0])
        
        return CompleteQuestion(question=question, answer=answer)
    
    def get_random_game_questions(self, categories=None, count=10) -> List[CompleteQuestion]:
        """
        Get random questions for a game
        
        Args:
            categories (List[str], optional): Categories to include
            count (int): Number of questions
            
        Returns:
            List[CompleteQuestion]: Random questions with answers
        """
        # Build query for questions
        query = self.client.table(self.questions_table).select("*")
        
        # Filter by categories if provided
        if categories:
            query = query.in_("category", categories)
        
        # Get random questions
        response = query.order("created_at").limit(count).execute()
        
        if not response.data:
            return []
        
        questions = [Question.from_dict(data) for data in response.data]
        question_ids = [q.id for q in questions]
        
        # Get answers for these questions
        answers_response = (
            self.client
            .table(self.answers_table)
            .select("*")
            .in_("question_id", question_ids)
            .execute()
        )
        
        # Create a mapping of question_id to answer
        answer_map = {}
        for data in answers_response.data:
            answer = Answer.from_dict(data)
            answer_map[answer.question_id] = answer
        
        # Combine questions with answers
        complete_questions = []
        for question in questions:
            if question.id in answer_map:
                complete_questions.append(
                    CompleteQuestion(
                        question=question,
                        answer=answer_map[question.id]
                    )
                )
        
        return complete_questions