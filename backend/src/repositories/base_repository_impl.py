# backend/src/repositories/base_repository_impl.py
import uuid
from typing import List, Optional, Type, Dict, Any, Union
from pydantic import BaseModel
from supabase_py_async import AsyncClient # Use async client
from postgrest import APIResponse

from .base_repository import BaseRepository, ModelType, CreateSchemaType, UpdateSchemaType, IdentifierType

class BaseRepositoryImpl(BaseRepository[ModelType, CreateSchemaType, UpdateSchemaType, IdentifierType]):
    """
    Generic implementation of the BaseRepository using Supabase.

    This class provides concrete implementations for the CRUD operations
    defined in BaseRepository, interacting with a Supabase table.
    """

    def __init__(self, *, model: Type[ModelType], db: AsyncClient, table_name: str):
        """
        Initialize the repository.

        Args:
            model: The Pydantic model type for this repository.
            db: An instance of the Supabase async client.
            table_name: The name of the Supabase table this repository manages.
        """
        self.model = model
        self.db = db
        self.table_name = table_name

    async def _execute_query(self, query) -> APIResponse:
        """Helper to execute supabase query and handle potential errors."""
        try:
            response = await query.execute()
            # Basic check if Supabase returned data or an error structure
            # Adjust based on actual supabase-py async error handling if needed
            if hasattr(response, 'error') and response.error:
                 raise ValueError(f"Supabase query failed: {response.error}")
            if not hasattr(response, 'data'):
                 raise ValueError(f"Supabase response format unexpected: {response}")
            return response
        except Exception as e:
            # Log the error appropriately in a real application
            print(f"Error executing Supabase query: {e}")
            # Depending on desired behaviour, re-raise or return None/empty
            raise # Re-raise for now

    async def get_by_id(self, id: IdentifierType) -> Optional[ModelType]:
        query = self.db.table(self.table_name).select("*").eq("id", str(id)).limit(1)
        response = await self._execute_query(query)

        if response.data:
            return self.model.parse_obj(response.data[0])
        return None

    async def get_all(self, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        query = self.db.table(self.table_name).select("*").offset(skip).limit(limit)
        response = await self._execute_query(query)

        return [self.model.parse_obj(item) for item in response.data]

    async def create(self, *, obj_in: CreateSchemaType) -> ModelType:
        # Use exclude_unset=False to include default values if needed, adjust as necessary
        # Ensure enums are converted to their values if needed (Pydantic usually handles this)
        insert_data = obj_in.dict(exclude_unset=False, by_alias=False)
        # Convert UUIDs/datetimes to strings if Supabase client requires it (often not needed)
        # Example (if needed): insert_data['id'] = str(insert_data['id'])

        query = self.db.table(self.table_name).insert(insert_data, returning='representation') # return the inserted row
        response = await self._execute_query(query)

        if response.data:
            return self.model.parse_obj(response.data[0])
        else:
            # This case should ideally not happen with 'returning=representation' on success
            raise ValueError("Failed to create object, no data returned.")


    async def update(self, *, id: IdentifierType, obj_in: UpdateSchemaType) -> Optional[ModelType]:
        # Use exclude_unset=True for partial updates
        update_data = obj_in.dict(exclude_unset=True, by_alias=False)

        if not update_data:
            # If there's nothing to update, maybe return the existing object or None
            return await self.get_by_id(id) # Or raise an error / return None

        query = self.db.table(self.table_name).update(update_data).eq("id", str(id)).returning('representation')
        response = await self._execute_query(query)

        if response.data:
            return self.model.parse_obj(response.data[0])
        return None # Return None if the row with the ID didn't exist

    async def delete(self, *, id: IdentifierType) -> Optional[ModelType]:
        # Optionally return the deleted object
        query = self.db.table(self.table_name).delete().eq("id", str(id)).returning('representation')
        response = await self._execute_query(query)

        if response.data:
            return self.model.parse_obj(response.data[0])
        return None # Return None if the row didn't exist