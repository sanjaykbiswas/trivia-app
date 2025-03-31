# backend/src/repositories/pack_group_repository.py
import uuid
from typing import Optional
from supabase import AsyncClient

from ..models.pack_group import PackGroup, PackGroupCreate, PackGroupUpdate
from .base_repository_impl import BaseRepositoryImpl
from ..utils import ensure_uuid

class PackGroupRepository(BaseRepositoryImpl[PackGroup, PackGroupCreate, PackGroupUpdate, uuid.UUID]):
    """
    Repository for managing PackGroup data in Supabase.
    """
    def __init__(self, db: AsyncClient):
        super().__init__(model=PackGroup, db=db, table_name="pack_groups") # Table name: "pack_groups"

    # --- Custom PackGroup-specific methods (if any) ---
    async def get_by_name(self, name: str) -> Optional[PackGroup]:
        """Retrieve a pack group by its name."""
        query = self.db.table(self.table_name).select("*").eq("name", name).limit(1)
        response = await self._execute_query(query)
        if response.data:
            return self.model.parse_obj(response.data[0])
        return None