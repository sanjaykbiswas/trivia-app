# backend/src/repositories/base_repository_impl.py
import uuid
from typing import List, Optional, Type, Dict, Any, Union, TypeVar
from pydantic import BaseModel
from supabase import AsyncClient
from postgrest import APIResponse

from .base_repository import BaseRepository, ModelType, CreateSchemaType, UpdateSchemaType, IdentifierType
from ..utils import ensure_uuid

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
            db: An instance of the Supabase AsyncClient.
            table_name: The name of the Supabase table this repository manages.
        """
        self.model = model
        self.db = db
        self.table_name = table_name

    def _serialize_data_for_db(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively serialize data for database storage.
        
        Args:
            data: Dictionary containing data to serialize
            
        Returns:
            Serialized dictionary ready for database insertion
        """
        result = {}
        
        for key, value in data.items():
            # Handle lists
            if isinstance(value, list):
                result[key] = [
                    self._serialize_data_for_db(item) if isinstance(item, dict) else item 
                    for item in value
                ]
            # Handle nested dictionaries
            elif isinstance(value, dict):
                result[key] = self._serialize_data_for_db(value)
            # Handle other types
            else:
                result[key] = value
                
        return result

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
        """Get a record by ID."""
        # Ensure id is a valid UUID string
        id_str = ensure_uuid(id)
        
        query = self.db.table(self.table_name).select("*").eq("id", id_str).limit(1)
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
        
        # Serialize data for database
        insert_data = self._serialize_data_for_db(insert_data)

        # Step 1: Insert the data
        query = self.db.table(self.table_name).insert(insert_data)
        response = await self._execute_query(query)

        # Step 2: If successful and we have an id, fetch the newly created record
        if response.data and 'id' in response.data[0]:
            new_id = response.data[0]['id']
            fetch_query = self.db.table(self.table_name).select("*").eq("id", new_id).limit(1)
            fetch_response = await self._execute_query(fetch_query)
            
            if fetch_response.data:
                return self.model.parse_obj(fetch_response.data[0])
                
        # If we couldn't get the full record data, try to use the insert response
        if response.data:
            try:
                return self.model.parse_obj(response.data[0])
            except Exception as e:
                print(f"Warning: Could not parse insert response: {e}")
                
        # As a last resort, use the input data (but this might miss default values)
        return self.model.parse_obj(insert_data)

    async def update(self, *, id: IdentifierType, obj_in: UpdateSchemaType) -> Optional[ModelType]:
        """Update a record with proper handling of optional fields."""
        # Ensure id is a valid UUID string
        id_str = ensure_uuid(id)
        
        # Use exclude_unset=True for partial updates and exclude None values
        update_data = obj_in.dict(exclude_unset=True, exclude_none=True, by_alias=False)

        if not update_data:
            # If there's nothing to update, return the existing object
            return await self.get_by_id(id)

        # Serialize data for database
        update_data = self._serialize_data_for_db(update_data)

        # Step 1: Update the record
        query = self.db.table(self.table_name).update(update_data).eq("id", id_str)
        await self._execute_query(query)

        # Step 2: Fetch the updated record
        return await self.get_by_id(id)

    async def delete(self, *, id: IdentifierType) -> Optional[ModelType]:
        """Delete a record and return the deleted object if successful."""
        # Ensure id is a valid UUID string
        id_str = ensure_uuid(id)
        
        # Step 1: Get the object before deletion
        obj = await self.get_by_id(id)
        
        if not obj:
            return None  # Object doesn't exist
            
        # Step 2: Delete the object
        query = self.db.table(self.table_name).delete().eq("id", id_str)
        await self._execute_query(query)
        
        # Step 3: Return the object that was deleted
        return obj