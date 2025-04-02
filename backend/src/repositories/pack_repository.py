# backend/src/repositories/pack_repository.py
import uuid
from typing import List, Optional, Dict, Any
from supabase import AsyncClient
import logging # Added logging

from ..models.pack import Pack, PackCreate, PackUpdate, CreatorType
from .base_repository_impl import BaseRepositoryImpl
from ..utils import ensure_uuid

# Configure logger
logger = logging.getLogger(__name__)

class PackRepository(BaseRepositoryImpl[Pack, PackCreate, PackUpdate, str]):
    """
    Repository for managing Pack data in Supabase.
    Includes fields previously in PackCreationData.
    """
    def __init__(self, db: AsyncClient):
        super().__init__(model=Pack, db=db, table_name="packs")

    # Helper method to ensure enum values are properly serialized
    def _serialize_enum_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert any enums to their string values for storage."""
        result = data.copy()
        if 'creator_type' in result and isinstance(result['creator_type'], CreatorType):
            result['creator_type'] = result['creator_type'].value
        return result

    async def get_by_pack_group_id(self, pack_group_id: str, *, skip: int = 0, limit: int = 100) -> List[Pack]:
        """Retrieve packs associated with a specific PackGroup ID (checks list)."""
        pack_group_id_str = ensure_uuid(pack_group_id)

        query = (
            self.db.table(self.table_name)
            .select("*")
            .cs("pack_group_id", [pack_group_id_str]) # Use contains operator for array
            .offset(skip)
            .limit(limit)
            .order("created_at", desc=True)
        )
        response = await self._execute_query(query)
        # Use model_validate for Pydantic V2
        return [self.model.model_validate(item) for item in response.data]

    async def get_by_creator_type(self, creator_type: CreatorType, *, skip: int = 0, limit: int = 100) -> List[Pack]:
        """Retrieve packs by their creator type."""
        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("creator_type", creator_type.value)
            .offset(skip)
            .limit(limit)
            .order("created_at", desc=True)
        )
        response = await self._execute_query(query)
        # Use model_validate for Pydantic V2
        return [self.model.model_validate(item) for item in response.data]

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
        # Use model_validate for Pydantic V2
        return [self.model.model_validate(item) for item in response.data]

    async def update_correct_answer_rate(self, pack_id: str, rate: float) -> Optional[Pack]:
        """Updates the correct answer rate for a given pack."""
        pack_id_str = ensure_uuid(pack_id)
        update_data = {"correct_answer_rate": rate}
        query = self.db.table(self.table_name).update(update_data).eq("id", pack_id_str)
        await self._execute_query(query)
        return await self.get_by_id(pack_id_str) # Fetch updated record

    # Override base methods to handle enum serialization and new fields if needed
    async def create(self, *, obj_in: PackCreate) -> Pack:
        """Create a new pack with proper enum handling and new fields."""
        # Use exclude_none=True to avoid inserting None for optional fields
        # Ensure defaults from the model are used if not provided in obj_in
        insert_data = obj_in.model_dump(exclude_unset=False, exclude_none=True, by_alias=False)
        insert_data = self._serialize_enum_values(insert_data) # Handle enums
        insert_data = self._serialize_data_for_db(insert_data) # Handle potential nested JSON

        # Set default values if not present
        if 'seed_questions' not in insert_data:
            insert_data['seed_questions'] = {}
        if 'custom_difficulty_description' not in insert_data:
            insert_data['custom_difficulty_description'] = {}

        # --- MODIFIED LINE: Reinstate await ---
        query_result = await self.db.table(self.table_name).insert(insert_data).execute()
        # --- END MODIFIED LINE ---

        # Fetch the newly created record to get all fields including defaults
        # --- MODIFIED LINE: Use query_result instead of query ---
        if query_result.data:
             # --- MODIFIED LINE: Use query_result instead of query ---
             new_id = query_result.data[0].get('id')
             if new_id:
                 # Fetch the complete record
                 logger.debug(f"Fetching newly created pack with ID: {new_id}")
                 new_pack = await self.get_by_id(new_id)
                 if new_pack:
                      return new_pack
                 else:
                      logger.warning(f"Failed to fetch pack {new_id} after creation, attempting to parse insert response.")
             # Fallback: parse insert response (might miss DB defaults)
             try:
                  # --- MODIFIED LINE: Use query_result instead of query ---
                  return self.model.model_validate(query_result.data[0])
             except Exception as e:
                  logger.error(f"Failed to parse insert response: {e}")
                  raise ValueError("Failed to create pack, could not retrieve or parse result.")

        else:
            # --- MODIFIED LINE: Use query_result instead of query ---
            logger.error(f"Failed to create pack, no data returned from insert operation. Error: {getattr(query_result, 'error', 'Unknown error')}")
            raise ValueError(f"Failed to create pack, no data returned. Error: {getattr(query_result, 'error', 'Unknown error')}")


    async def update(self, *, id: str, obj_in: PackUpdate) -> Optional[Pack]:
        """Update an existing pack with proper enum handling and new fields."""
        id_str = ensure_uuid(id)
        # Use exclude_unset=True for partial updates
        update_data = obj_in.model_dump(exclude_unset=True, exclude_none=True, by_alias=False)

        if not update_data:
            return await self.get_by_id(id_str) # Return current if no update data

        update_data = self._serialize_enum_values(update_data) # Handle enums
        update_data = self._serialize_data_for_db(update_data) # Handle potential nested JSON

        query = self.db.table(self.table_name).update(update_data).eq("id", id_str)
        await self._execute_query(query) # Base implementation handles await correctly

        return await self.get_by_id(id_str) # Fetch and return updated record