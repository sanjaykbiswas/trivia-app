from typing import List, Dict, Any, Optional
import json
from models.question import Question
from models.answer import Answer
from models.complete_question import CompleteQuestion
from repositories.base_repository import BaseRepository
from repositories.category_repository import CategoryRepository
from config.environment import Environment

class QuestionRepository(BaseRepository[Question]):
    """
    Repository for managing trivia questions in Supabase
    """
    def __init__(self, supabase_client, category_repository=None):
        self.client = supabase_client
        self.questions_table = "questions"
        self.answers_table = "answers"
        # Store the category repository for lookups
        self.category_repository = category_repository

    async def get_category_repository(self):
        """
        Lazy initialization of category repository if not provided
        
        Returns:
            CategoryRepository: Repository for category operations
        """
        if not self.category_repository:
            from repositories.category_repository import CategoryRepository
            self.category_repository = CategoryRepository(self.client)
        return self.category_repository
    
    async def create(self, question: Question) -> Question:
        """
        Create a single question
        
        Args:
            question (Question): Question to create
            
        Returns:
            Question: Created question with ID
        """
        # Ensure category_id is set if we only have category_name
        if not question.category_id and question.category_name:
            await self._ensure_category_id(question)
            
        response = (
            self.client
            .table(self.questions_table)
            .insert(question.to_dict())
            .execute()
        )
        
        if response.data:
            question.id = response.data[0]["id"]
        
        return question
    
    async def _ensure_category_id(self, question: Question) -> None:
        """
        Ensure question has a valid category_id
        
        Args:
            question (Question): Question to update with category_id
        """
        if question.category_id:
            return
            
        if not question.category_name:
            # Default to general knowledge if no category info provided
            question.category_name = "General Knowledge"
            
        # Get category repository
        category_repo = await self.get_category_repository()
        
        # Try to find category by name
        category = await category_repo.get_by_name(question.category_name)
        
        if category:
            # Found existing category
            question.category_id = category.id
        else:
            # Create new category if not found
            try:
                new_category = await category_repo.create_category_by_name(question.category_name)
                question.category_id = new_category.id
            except Exception as e:
                # If creation fails, use a default category ID
                # In a real app, we might want to handle this differently
                default_category = await category_repo.get_or_create_default_category()
                question.category_id = default_category.id
    
    async def bulk_create(self, questions: List[Question]) -> List[Question]:
        """
        Create multiple questions
        
        Args:
            questions (List[Question]): Questions to create
            
        Returns:
            List[Question]: Created questions with IDs
        """
        # Ensure all questions have category_ids
        for question in questions:
            await self._ensure_category_id(question)
            
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
    
    async def get_by_id(self, id: str) -> Optional[Question]:
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
            .select("*, categories(name)")  # Join with categories to get name
            .eq("id", id)
            .execute()
        )
        
        if response.data:
            question_data = response.data[0]
            
            # Extract category name from joined data if available
            if "categories" in question_data and question_data["categories"]:
                question_data["category_name"] = question_data["categories"]["name"]
            
            # Remove the joined object to avoid dataclass conflicts
            if "categories" in question_data:
                del question_data["categories"]
                
            return Question.from_dict(question_data)
        
        return None
    
    async def find(self, filter_params: Dict[str, Any], limit: int = 100) -> List[Question]:
        """
        Find questions matching criteria
        
        Args:
            filter_params (Dict[str, Any]): Filter criteria
            limit (int): Maximum results
            
        Returns:
            List[Question]: Matching questions
        """
        query = self.client.table(self.questions_table).select("*, categories(name)")
        
        # Apply filters
        for key, value in filter_params.items():
            query = query.eq(key, value)
        
        response = query.limit(limit).execute()
        
        questions = []
        for data in response.data:
            # Extract category name from joined data if available
            if "categories" in data and data["categories"]:
                data["category_name"] = data["categories"]["name"]
            
            # Remove the joined object to avoid dataclass conflicts
            if "categories" in data:
                del data["categories"]
                
            questions.append(Question.from_dict(data))
            
        return questions
    
    async def find_by_category(self, category_id: str, limit: int = 50) -> List[Question]:
        """
        Find questions by category ID
        
        Args:
            category_id (str): Category ID to filter by
            limit (int): Maximum results
            
        Returns:
            List[Question]: Matching questions
        """
        return await self.find({"category_id": category_id}, limit)
    
    async def find_by_category_name(self, category_name: str, limit: int = 50) -> List[Question]:
        """
        Find questions by category name
        
        Args:
            category_name (str): Category name to find
            limit (int): Maximum results
            
        Returns:
            List[Question]: Matching questions
        """
        # First find the category ID by name
        category_repo = await self.get_category_repository()
        category = await category_repo.get_by_name(category_name)
        
        if not category:
            return []  # Category not found
            
        # Then find questions by category ID
        return await self.find_by_category(category.id, limit)
    
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Question]:
        """
        Update a question
        
        Args:
            id (str): Question ID
            data (Dict[str, Any]): Update data
            
        Returns:
            Optional[Question]: Updated question
        """
        # If updating category_name, ensure category_id is updated too
        if "category_name" in data and "category_id" not in data:
            category_repo = await self.get_category_repository()
            category = await category_repo.get_by_name(data["category_name"])
            
            if category:
                data["category_id"] = category.id
            else:
                # Create new category if needed
                try:
                    new_category = await category_repo.create_category_by_name(data["category_name"])
                    data["category_id"] = new_category.id
                except Exception:
                    # Keep the existing category_id if we can't update it
                    pass
        
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
    
    async def delete(self, id: str) -> bool:
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
    
    async def save_answer(self, answer: Answer) -> Answer:
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
    
    async def bulk_save_answers(self, answers: List[Answer]) -> List[Answer]:
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
    
    async def get_complete_question(self, question_id: str) -> Optional[CompleteQuestion]:
        """
        Get a question with its answer
        
        Args:
            question_id (str): Question ID
            
        Returns:
            Optional[CompleteQuestion]: Complete question if found
        """
        # Get question
        question = await self.get_by_id(question_id)
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
    
    async def get_random_game_questions(self, categories=None, count=10) -> List[CompleteQuestion]:
        """
        Get random questions for a game
        
        Args:
            categories (List[str], optional): Category IDs to include
            count (int): Number of questions
            
        Returns:
            List[CompleteQuestion]: Random questions with answers
        """
        # Build query for questions
        query = self.client.table(self.questions_table).select("*, categories(name)")
        
        # Filter by categories if provided
        if categories:
            query = query.in_("category_id", categories)
        
        # Get random questions
        response = query.order("created_at").limit(count).execute()
        
        if not response.data:
            return []
        
        questions = []
        for data in response.data:
            # Extract category name from joined data if available
            if "categories" in data and data["categories"]:
                data["category_name"] = data["categories"]["name"]
            
            # Remove the joined object to avoid dataclass conflicts
            if "categories" in data:
                del data["categories"]
                
            questions.append(Question.from_dict(data))
            
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