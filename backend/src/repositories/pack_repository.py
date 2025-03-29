# backend/src/repositories/pack_repository.py
import uuid
from typing import List, Optional
from supabase_py_async import AsyncClient

from ..models.pack import Pack, CreatorType
from .base_repository_impl import BaseRepositoryImpl

class PackRepository(BaseRepositoryImpl[Pack, Pack, Pack, uuid.UUID]):
    """
    Repository for managing Pack data in Supabase.
    """
    def __init__(self, db: AsyncClient):
        super().__init__(model=Pack, db=db, table_name="packs") # Table name: "packs"

    # --- Custom Pack-specific methods ---

    async def get_by_category_id(self, category_id: uuid.UUID, *, skip: int = 0, limit: int = 100) -> List[Pack]:
        """Retrieve packs belonging to a specific category (PackGroup)."""
        # Supabase array contains query: cs.{column_name}
        query = (
            self.db.table(self.table_name)
            .select("*")
            .cs("category_id", [str(category_id)]) # Check if category_id array contains the UUID
            .offset(skip)
            .limit(limit)
        )
        response = await self._execute_query(query)
        return [self.model.parse_obj(item) for item in response.data]

    async def get_by_creator_type(self, creator_type: CreatorType, *, skip: int = 0, limit: int = 100) -> List[Pack]:
        """Retrieve packs by their creator type."""
        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("creator_type", creator_type.value)
            .offset(skip)
            .limit(limit)
        )
        response = await self._execute_query(query)
        return [self.model.parse_obj(item) for item in response.data]

    async def search_by_name(self, name_query: str, *, skip: int = 0, limit: int = 100) -> List[Pack]:
        """Search for packs by name (case-insensitive partial match)."""
        query = (
            self.db.table(self.table_name)
            .select("*")
            .ilike("name", f"%{name_query}%") # Case-insensitive LIKE
            .offset(skip)
            .limit(limit)
        )
        response = await self._execute_query(query)
        return [self.model.parse_obj(item) for item in response.data]

    async def update_correct_answer_rate(self, pack_id: uuid.UUID, rate: float) -> Optional[Pack]:
        """Updates the correct answer rate for a given pack."""
        update_data = {"correct_answer_rate": rate}
        query = self.db.table(self.table_name).update(update_data).eq("id", str(pack_id)).returning('representation')
        response = await self._execute_query(query)
        if response.data:
            return self.model.parse_obj(response.data[0])
        return None