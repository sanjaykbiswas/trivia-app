# backend/src/repositories/user_question_history_repository.py
import uuid
from typing import List, Optional
from supabase import AsyncClient

from ..models.user_question_history import UserQuestionHistory, UserQuestionHistoryCreate, UserQuestionHistoryUpdate
from .base_repository_impl import BaseRepositoryImpl
from ..utils import ensure_uuid

class UserQuestionHistoryRepository(BaseRepositoryImpl[UserQuestionHistory, UserQuestionHistoryCreate, UserQuestionHistoryUpdate, str]):
    """
    Repository for managing UserQuestionHistory data in Supabase.
    """
    def __init__(self, db: AsyncClient):
        super().__init__(model=UserQuestionHistory, db=db, table_name="user_question_history") # Table name: "user_question_history"

    # --- Custom UserQuestionHistory-specific methods ---

    async def get_by_user_id(self, user_id: str, *, skip: int = 0, limit: int = 100) -> List[UserQuestionHistory]:
        """Retrieve history entries for a specific user."""
        # Ensure user_id is a valid UUID string
        user_id_str = ensure_uuid(user_id)
        
        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("user_id", user_id_str)
            .order("created_at", desc=True) # Optional: order by date
            .offset(skip)
            .limit(limit)
        )
        response = await self._execute_query(query)
        return [self.model.parse_obj(item) for item in response.data]

    async def get_by_question_id(self, question_id: str, *, skip: int = 0, limit: int = 100) -> List[UserQuestionHistory]:
        """Retrieve history entries for a specific question."""
        # Ensure question_id is a valid UUID string
        question_id_str = ensure_uuid(question_id)
        
        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("question_id", question_id_str)
            .order("created_at", desc=True)
            .offset(skip)
            .limit(limit)
        )
        response = await self._execute_query(query)
        return [self.model.parse_obj(item) for item in response.data]

    async def get_by_user_and_question(self, user_id: str, question_id: str) -> List[UserQuestionHistory]:
        """Retrieve all history entries for a specific user and question."""
        # Ensure UUIDs are valid UUID strings
        user_id_str = ensure_uuid(user_id)
        question_id_str = ensure_uuid(question_id)
        
        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("user_id", user_id_str)
            .eq("question_id", question_id_str)
            .order("created_at", desc=True)
        )
        response = await self._execute_query(query)
        return [self.model.parse_obj(item) for item in response.data]