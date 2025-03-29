# backend/src/repositories/question_repository.py
import uuid
from typing import List, Optional, Dict, Any
from supabase_py_async import AsyncClient

from ..models.question import Question, QuestionCreate, QuestionUpdate, DifficultyLevel
from .base_repository_impl import BaseRepositoryImpl


class QuestionRepository(BaseRepositoryImpl[Question, QuestionCreate, QuestionUpdate, uuid.UUID]):
    """
    Repository for managing Question data in Supabase.
    """
    def __init__(self, db: AsyncClient):
        super().__init__(model=Question, db=db, table_name="questions") # Table name: "questions"

    # Helper method to ensure enum values are properly serialized
    def _serialize_enum_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert any enums to their string values for storage."""
        result = data.copy()
        if 'difficulty_initial' in result and isinstance(result['difficulty_initial'], DifficultyLevel):
            result['difficulty_initial'] = result['difficulty_initial'].value
        if 'difficulty_current' in result and isinstance(result['difficulty_current'], DifficultyLevel):
            result['difficulty_current'] = result['difficulty_current'].value
        return result

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
        # Convert enum to string value for the query
        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("difficulty_current", difficulty.value)
            .offset(skip)
            .limit(limit)
        )
        response = await self._execute_query(query)
        return [self.model.parse_obj(item) for item in response.data]

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

    # Override base methods to handle enum serialization
    async def create(self, *, obj_in: QuestionCreate) -> Question:
        """Create a new question with proper enum handling."""
        insert_data = obj_in.dict(exclude_unset=False, by_alias=False)
        insert_data = self._serialize_enum_values(insert_data)
        
        query = self.db.table(self.table_name).insert(insert_data, returning='representation')
        response = await self._execute_query(query)

        if response.data:
            return self.model.parse_obj(response.data[0])
        else:
            raise ValueError("Failed to create question, no data returned.")

    async def update(self, *, id: uuid.UUID, obj_in: QuestionUpdate) -> Optional[Question]:
        """Update an existing question with proper enum handling."""
        update_data = obj_in.dict(exclude_unset=True, exclude_none=True, by_alias=False)
        
        if not update_data:
            return await self.get_by_id(id)
            
        update_data = self._serialize_enum_values(update_data)
        
        query = self.db.table(self.table_name).update(update_data).eq("id", str(id)).returning('representation')
        response = await self._execute_query(query)

        if response.data:
            return self.model.parse_obj(response.data[0])
        return None