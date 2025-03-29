# backend/src/repositories/base_repository_impl.py
import uuid
from typing import List, Optional, Type, Dict, Any, Union, TypeVar
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
        """Get a record by ID with proper conversion of UUID to string."""
        query = self.db.table(self.table_name).select("*").eq("id", str(id)).limit(1)
        response = await self._execute_query(query)

        if response.data:
            return self.model.parse_obj(response.data[0])
        return None

    async def get_all(self, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Get all records with pagination."""
        query = self.db.table(self.table_name).select("*").offset(skip).limit(limit)
        response = await self._execute_query(query)

        return [self.model.parse_obj(item) for item in response.data]

    async def create(self, *, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record from a creation schema."""
        # Convert model to dict and prepare for insertion
        insert_data = obj_in.dict(exclude_unset=False, by_alias=False)
        
        # Handle UUIDs by converting to strings
        for key, value in insert_data.items():
            if isinstance(value, uuid.UUID):
                insert_data[key] = str(value)

        query = self.db.table(self.table_name).insert(insert_data, returning='representation') # return the inserted row
        response = await self._execute_query(query)

        if response.data:
            return self.model.parse_obj(response.data[0])
        else:
            # This case should ideally not happen with 'returning=representation' on success
            raise ValueError("Failed to create object, no data returned.")

    async def update(self, *, id: IdentifierType, obj_in: UpdateSchemaType) -> Optional[ModelType]:
        """Update a record with proper handling of optional fields."""
        # Use exclude_unset=True for partial updates and exclude None values
        update_data = obj_in.dict(exclude_unset=True, exclude_none=True, by_alias=False)

        if not update_data:
            # If there's nothing to update, return the existing object
            return await self.get_by_id(id)

        # Handle UUIDs by converting to strings
        for key, value in update_data.items():
            if isinstance(value, uuid.UUID):
                update_data[key] = str(value)

        query = self.db.table(self.table_name).update(update_data).eq("id", str(id)).returning('representation')
        response = await self._execute_query(query)

        if response.data:
            return self.model.parse_obj(response.data[0])
        return None # Return None if the row with the ID didn't exist

    async def delete(self, *, id: IdentifierType) -> Optional[ModelType]:
        """Delete a record and return the deleted object if successful."""
        query = self.db.table(self.table_name).delete().eq("id", str(id)).returning('representation')
        response = await self._execute_query(query)

        if response.data:
            return self.model.parse_obj(response.data[0])
        return None # Return None if the row didn't exist