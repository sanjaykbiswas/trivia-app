# backend/src/repositories/pack_repository.py
import uuid
from typing import List, Optional, Dict, Any
from supabase_py_async import AsyncClient

from ..models.pack import Pack, PackCreate, PackUpdate, CreatorType
from .base_repository_impl import BaseRepositoryImpl

class PackRepository(BaseRepositoryImpl[Pack, PackCreate, PackUpdate, uuid.UUID]):
    """
    Repository for managing Pack data in Supabase.
    """
    def __init__(self, db: AsyncClient):
        super().__init__(model=Pack, db=db, table_name="packs") # Table name: "packs"

    # Helper method to ensure enum values are properly serialized
    def _serialize_enum_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert any enums to their string values for storage."""
        result = data.copy()
        if 'creator_type' in result and isinstance(result['creator_type'], CreatorType):
            result['creator_type'] = result['creator_type'].value
        
        # Handle UUID lists
        if 'pack_group_id' in result and isinstance(result['pack_group_id'], list):
            result['pack_group_id'] = [str(uuid_val) for uuid_val in result['pack_group_id'] if uuid_val is not None]
            
        return result

    async def get_by_pack_group_id(self, pack_group_id: uuid.UUID, *, skip: int = 0, limit: int = 100) -> List[Pack]:
        """Retrieve packs associated with a specific PackGroup ID (checks list)."""
        query = (
            self.db.table(self.table_name)
            .select("*")
            .cs("pack_group_id", [str(pack_group_id)])
            .offset(skip)
            .limit(limit)
            .order("created_at", desc=True)
        )
        response = await self._execute_query(query)
        return [self.model.parse_obj(item) for item in response.data]

    async def get_by_creator_type(self, creator_type: CreatorType, *, skip: int = 0, limit: int = 100) -> List[Pack]:
        """Retrieve packs by their creator type."""
        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("creator_type", creator_type.value) # Properly use enum value
            .offset(skip)
            .limit(limit)
            .order("created_at", desc=True)
        )
        response = await self._execute_query(query)
        return [self.model.parse_obj(item) for item in response.data]

    async def search_by_name(self, name_query: str, *, skip: int = 0, limit: int = 100) -> List[Pack]:
        """Search for packs by name (case-insensitive partial match)."""
        query = (
            self.db.table(self.table_name)
            .select("*")
            .ilike("name", f"%{name_query}%")
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

    # Override base methods to handle enum serialization
    async def create(self, *, obj_in: PackCreate) -> Pack:
        """Create a new pack with proper enum handling."""
        insert_data = obj_in.dict(exclude_unset=False, by_alias=False)
        insert_data = self._serialize_enum_values(insert_data)
        
        query = self.db.table(self.table_name).insert(insert_data, returning='representation')
        response = await self._execute_query(query)

        if response.data:
            return self.model.parse_obj(response.data[0])
        else:
            raise ValueError("Failed to create pack, no data returned.")

    async def update(self, *, id: uuid.UUID, obj_in: PackUpdate) -> Optional[Pack]:
        """Update an existing pack with proper enum handling."""
        update_data = obj_in.dict(exclude_unset=True, exclude_none=True, by_alias=False)
        
        if not update_data:
            return await self.get_by_id(id)
            
        update_data = self._serialize_enum_values(update_data)
        
        query = self.db.table(self.table_name).update(update_data).eq("id", str(id)).returning('representation')
        response = await self._execute_query(query)

        if response.data:
            return self.model.parse_obj(response.data[0])
        return None