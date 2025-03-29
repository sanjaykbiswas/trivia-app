# backend/src/repositories/incorrect_answers_repository.py
import uuid
from typing import Optional, List
from supabase_py_async import AsyncClient

from ..models.incorrect_answers import IncorrectAnswers, IncorrectAnswersCreate, IncorrectAnswersUpdate
from .base_repository_impl import BaseRepositoryImpl

class IncorrectAnswersRepository(BaseRepositoryImpl[IncorrectAnswers, IncorrectAnswersCreate, IncorrectAnswersUpdate, uuid.UUID]):
    """
    Repository for managing IncorrectAnswers data in Supabase.
    """
    def __init__(self, db: AsyncClient):
        super().__init__(model=IncorrectAnswers, db=db, table_name="incorrect_answers") # Table name: "incorrect_answers"

    # --- Custom IncorrectAnswers-specific methods ---

    async def get_by_question_id(self, question_id: uuid.UUID) -> Optional[IncorrectAnswers]:
        """Retrieve incorrect answers for a specific question."""
        # Assuming only one set of incorrect answers per question_id
        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("question_id", str(question_id))
            .limit(1) # Expecting only one entry per question
        )
        response = await self._execute_query(query)
        if response.data:
            return self.model.parse_obj(response.data[0])
        return None

    async def delete_by_question_id(self, question_id: uuid.UUID) -> List[IncorrectAnswers]:
        """Deletes incorrect answers associated with a specific question_id."""
        # Deletes potentially multiple, returns list of deleted items
        query = (
            self.db.table(self.table_name)
            .delete()
            .eq("question_id", str(question_id))
            .returning('representation')
        )
        response = await self._execute_query(query)
        return [self.model.parse_obj(item) for item in response.data]