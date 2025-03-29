# backend/src/repositories/question_repository.py
import uuid
from typing import List, Optional
from supabase_py_async import AsyncClient

from ..models.question import Question, DifficultyLevel
from .base_repository_impl import BaseRepositoryImpl

class QuestionRepository(BaseRepositoryImpl[Question, Question, Question, uuid.UUID]):
    """
    Repository for managing Question data in Supabase.
    """
    def __init__(self, db: AsyncClient):
        super().__init__(model=Question, db=db, table_name="questions") # Table name: "questions"

    # --- Custom Question-specific methods ---

    async def get_by_pack_id(self, pack_id: uuid.UUID, *, skip: int = 0, limit: int = 100) -> List[Question]:
        """Retrieve questions belonging to a specific pack."""
        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("pack_id", str(pack_id))
            .offset(skip)
            .limit(limit)
        )
        response = await self._execute_query(query)
        return [self.model.parse_obj(item) for item in response.data]

    async def get_by_difficulty(self, difficulty: DifficultyLevel, *, skip: int = 0, limit: int = 100) -> List[Question]:
        """Retrieve questions by their current difficulty level."""
        # Assuming difficulty is stored as string in DB matching the Enum value
        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("difficulty_current", difficulty.value)
            .offset(skip)
            .limit(limit)
        )
        response = await self._execute_query(query)
        return [self.model.parse_obj(item) for item in response.data]

    # You might add methods to update difficulty_current or correct_answer_rate based on game results
    async def update_statistics(self, question_id: uuid.UUID, correct_rate: float, new_difficulty: Optional[DifficultyLevel] = None) -> Optional[Question]:
        """Updates the statistics for a given question."""
        update_data = {"correct_answer_rate": correct_rate}
        if new_difficulty:
            update_data["difficulty_current"] = new_difficulty.value

        query = self.db.table(self.table_name).update(update_data).eq("id", str(question_id)).returning('representation')
        response = await self._execute_query(query)

        if response.data:
            return self.model.parse_obj(response.data[0])
        return None