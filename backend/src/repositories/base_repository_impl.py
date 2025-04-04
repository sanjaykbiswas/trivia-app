# backend/src/repositories/base_repository_impl.py

import uuid
import logging
import traceback
from typing import List, Optional, Type, Dict, Any, Union, TypeVar
from pydantic import BaseModel
from supabase import AsyncClient
from postgrest import APIResponse
# --- Import datetime and timezone ---
from datetime import datetime, timezone

from .base_repository import BaseRepository, ModelType, CreateSchemaType, UpdateSchemaType, IdentifierType
from ..utils import ensure_uuid

# Configure logger
logger = logging.getLogger(__name__)

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
        logger.info(f"Initialized repository for table: {table_name}")

    # --- MODIFIED: Serialize datetimes within this helper ---
    def _serialize_data_for_db(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively serialize data for database storage, converting datetimes to ISO strings.

        Args:
            data: Dictionary containing data to serialize

        Returns:
            Serialized dictionary ready for database insertion/update
        """
        result = {}
        for key, value in data.items():
            if isinstance(value, datetime):
                # Ensure datetime is timezone-aware (use UTC if naive)
                # Supabase prefers timezone-aware timestamps ('timestamptz')
                if value.tzinfo is None:
                    value = value.replace(tzinfo=timezone.utc)
                # Convert to ISO 8601 string format
                result[key] = value.isoformat()
            elif isinstance(value, list):
                # Handle potential datetimes within lists
                result[key] = [
                    self._serialize_data_for_db(item) if isinstance(item, dict) else
                    (item.isoformat() if isinstance(item, datetime) else item)
                    for item in value
                ]
            elif isinstance(value, dict):
                result[key] = self._serialize_data_for_db(value) # Recurse for nested dicts
            # --- NEW: Handle Enums explicitly if needed (Pydantic v2 often handles this) ---
            # elif isinstance(value, Enum):
            #     result[key] = value.value
            # --- END NEW ---
            else:
                result[key] = value # Keep other types as is
        return result
    # --- END MODIFICATION ---

    async def _execute_query(self, query) -> APIResponse:
        """Helper to execute supabase query and handle potential errors."""
        try:
            logger.debug(f"Executing query on table {self.table_name}")
            response = await query.execute()
            # Basic check if Supabase returned data or an error structure
            if hasattr(response, 'error') and response.error:
                 logger.error(f"Supabase query failed: {response.error}")
                 raise ValueError(f"Supabase query failed: {response.error}")
            if not hasattr(response, 'data'):
                 # This case might happen for DELETE without returning data, allow it
                 if query.method == "DELETE":
                     logger.debug("DELETE query executed successfully, no data returned expectedly.")
                     # Create a dummy response object that mimics a successful no-data response
                     return APIResponse(data=[], count=None) # Return empty list for data
                 else:
                     logger.error(f"Supabase response format unexpected (no data attribute): {response}")
                     raise ValueError(f"Supabase response format unexpected: {response}")
            return response
        except Exception as e:
            logger.error(f"Error executing Supabase query on table {self.table_name}: {str(e)}")
            logger.error(traceback.format_exc())
            # Re-raise for proper error handling upstream
            raise

    async def get_by_id(self, id: IdentifierType) -> Optional[ModelType]:
        """Get a record by ID."""
        try:
            id_str = ensure_uuid(id)
            logger.debug(f"Getting record with ID: {id_str} from table {self.table_name}")

            query = self.db.table(self.table_name).select("*").eq("id", id_str).limit(1)
            response = await self._execute_query(query)

            if response.data:
                # Use model_validate for Pydantic V2
                return self.model.model_validate(response.data[0])
            logger.debug(f"No record found with ID: {id_str} in table {self.table_name}")
            return None
        except Exception as e:
            logger.error(f"Error getting record by ID {id} from table {self.table_name}: {str(e)}")
            raise

    async def get_all(self, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Get all records with pagination."""
        try:
            logger.debug(f"Getting records from table {self.table_name} (skip={skip}, limit={limit})")
            query = self.db.table(self.table_name).select("*").offset(skip).limit(limit)
            response = await self._execute_query(query)

             # Use model_validate for Pydantic V2
            return [self.model.model_validate(item) for item in response.data]
        except Exception as e:
            logger.error(f"Error getting all records from table {self.table_name}: {str(e)}")
            raise

    async def create(self, *, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record from a creation schema."""
        try:
            # Convert model to dict using Pydantic v2's model_dump
            insert_data = obj_in.model_dump(exclude_unset=False, by_alias=False)
            logger.debug(f"Creating new record in table {self.table_name}")

            # ---> FIX: Serialize data (including datetimes) before sending <---
            insert_data = self._serialize_data_for_db(insert_data)

            # Step 1: Insert the data
            query = self.db.table(self.table_name).insert(insert_data) # Pass serialized data
            response = await self._execute_query(query)

            # Step 2: If successful and we have an id, fetch the newly created record
            if response.data and 'id' in response.data[0]:
                new_id = response.data[0]['id']
                logger.debug(f"Record created with ID: {new_id}, fetching complete record")
                # Use get_by_id which handles parsing correctly
                new_record = await self.get_by_id(new_id)
                if new_record:
                    return new_record

            # Fallback: If fetching failed or no ID returned, try parsing insert response
            if response.data:
                try:
                    logger.warning("Could not fetch created record by ID, parsing insert response.")
                    # Use model_validate for Pydantic V2
                    return self.model.model_validate(response.data[0])
                except Exception as e:
                    logger.error(f"Could not parse insert response data: {e}")
                    raise ValueError("Failed to create record and parse response.")

            logger.error("Failed to create record, no data returned from insert.")
            raise ValueError("Failed to create record, no data returned.")

        except Exception as e:
            logger.error(f"Error creating record in table {self.table_name}: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    async def update(self, *, id: IdentifierType, obj_in: UpdateSchemaType) -> Optional[ModelType]:
        """Update a record with proper handling of optional fields."""
        try:
            id_str = ensure_uuid(id)
            logger.debug(f"Updating record with ID: {id_str} in table {self.table_name}")

            # Use Pydantic v2's model_dump for partial updates
            update_data = obj_in.model_dump(exclude_unset=True, exclude_none=True, by_alias=False)

            if not update_data:
                logger.debug(f"No fields to update for record {id_str}")
                return await self.get_by_id(id_str)

            # ---> FIX: Serialize data (including datetimes) before sending <---
            update_data = self._serialize_data_for_db(update_data)

            # Step 1: Update the record
            query = self.db.table(self.table_name).update(update_data).eq("id", id_str) # Pass serialized data
            await self._execute_query(query)

            # Step 2: Fetch the updated record
            logger.debug(f"Record updated, fetching updated record with ID: {id_str}")
            return await self.get_by_id(id_str)
        except Exception as e:
            logger.error(f"Error updating record with ID {id_str} in table {self.table_name}: {str(e)}") # Use id_str
            logger.error(traceback.format_exc())
            raise

    async def delete(self, *, id: IdentifierType) -> Optional[ModelType]:
        """Delete a record and return the deleted object if successful."""
        try:
            id_str = ensure_uuid(id)
            logger.debug(f"Deleting record with ID: {id_str} from table {self.table_name}")

            # Step 1: Get the object before deletion
            obj = await self.get_by_id(id_str)

            if not obj:
                logger.warning(f"Record with ID {id_str} not found for deletion")
                return None  # Object doesn't exist

            # Step 2: Delete the object
            query = self.db.table(self.table_name).delete().eq("id", id_str)
            await self._execute_query(query)

            # Step 3: Return the object that was deleted
            logger.debug(f"Successfully deleted record with ID: {id_str}")
            return obj
        except Exception as e:
            logger.error(f"Error deleting record with ID {id_str} in table {self.table_name}: {str(e)}") # Use id_str
            logger.error(traceback.format_exc())
            raise