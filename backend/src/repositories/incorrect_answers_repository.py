# backend/src/repositories/incorrect_answers_repository.py
import uuid
from typing import Optional, List
from supabase import AsyncClient

from ..models.incorrect_answers import IncorrectAnswers, IncorrectAnswersCreate, IncorrectAnswersUpdate
from .base_repository_impl import BaseRepositoryImpl
from ..utils import ensure_uuid

class IncorrectAnswersRepository(BaseRepositoryImpl[IncorrectAnswers, IncorrectAnswersCreate, IncorrectAnswersUpdate, str]):
    """
    Repository for managing IncorrectAnswers data in Supabase.
    """
    def __init__(self, db: AsyncClient):
        super().__init__(model=IncorrectAnswers, db=db, table_name="incorrect_answers") # Table name: "incorrect_answers"

    # --- Custom IncorrectAnswers-specific methods ---

    async def get_by_question_id(self, question_id: str) -> Optional[IncorrectAnswers]:
        """Retrieve incorrect answers for a specific question."""
        # Ensure question_id is a valid UUID string
        question_id_str = ensure_uuid(question_id)
        
        # Assuming only one set of incorrect answers per question_id
        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("question_id", question_id_str)
            .limit(1) # Expecting only one entry per question
        )
        response = await self._execute_query(query)
        if response.data:
            return self.model.parse_obj(response.data[0])
        return None

    async def delete_by_question_id(self, question_id: str) -> List[IncorrectAnswers]:
        """Deletes incorrect answers associated with a specific question_id."""
        # Ensure question_id is a valid UUID string
        question_id_str = ensure_uuid(question_id)
        
        # First, retrieve the records to be deleted
        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("question_id", question_id_str)
        )
        response = await self._execute_query(query)
        records = [self.model.parse_obj(item) for item in response.data]
        
        # Then delete them
        delete_query = (
            self.db.table(self.table_name)
            .delete()
            .eq("question_id", question_id_str)
        )
        await self._execute_query(delete_query)
        
        return records