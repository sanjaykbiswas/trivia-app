# backend/src/repositories/base_repository_impl.py
import uuid
import logging
import traceback
from typing import List, Optional, Type, Dict, Any, Union, TypeVar
from pydantic import BaseModel
from supabase import AsyncClient
from postgrest import APIResponse

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
            logger.debug(f"Executing query on table {self.table_name}")
            response = await query.execute()
            # Basic check if Supabase returned data or an error structure
            if hasattr(response, 'error') and response.error:
                 logger.error(f"Supabase query failed: {response.error}")
                 raise ValueError(f"Supabase query failed: {response.error}")
            if not hasattr(response, 'data'):
                 logger.error(f"Supabase response format unexpected: {response}")
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
            # Ensure id is a valid UUID string
            id_str = ensure_uuid(id)
            logger.debug(f"Getting record with ID: {id_str} from table {self.table_name}")
            
            query = self.db.table(self.table_name).select("*").eq("id", id_str).limit(1)
            response = await self._execute_query(query)

            if response.data:
                return self.model.parse_obj(response.data[0])
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

            return [self.model.parse_obj(item) for item in response.data]
        except Exception as e:
            logger.error(f"Error getting all records from table {self.table_name}: {str(e)}")
            raise

    async def create(self, *, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record from a creation schema."""
        try:
            # Convert model to dict and prepare for insertion
            insert_data = obj_in.dict(exclude_unset=False, by_alias=False)
            logger.debug(f"Creating new record in table {self.table_name}")
            
            # Serialize data for database
            insert_data = self._serialize_data_for_db(insert_data)

            # Step 1: Insert the data
            query = self.db.table(self.table_name).insert(insert_data)
            response = await self._execute_query(query)

            # Step 2: If successful and we have an id, fetch the newly created record
            if response.data and 'id' in response.data[0]:
                new_id = response.data[0]['id']
                logger.debug(f"Record created with ID: {new_id}, fetching complete record")
                fetch_query = self.db.table(self.table_name).select("*").eq("id", new_id).limit(1)
                fetch_response = await self._execute_query(fetch_query)
                
                if fetch_response.data:
                    return self.model.parse_obj(fetch_response.data[0])
                    
            # If we couldn't get the full record data, try to use the insert response
            if response.data:
                try:
                    logger.debug("Using insert response data for record")
                    return self.model.parse_obj(response.data[0])
                except Exception as e:
                    logger.warning(f"Could not parse insert response: {e}")
                    
            # As a last resort, use the input data (but this might miss default values)
            logger.warning("Using input data as fallback for created record")
            return self.model.parse_obj(insert_data)
        except Exception as e:
            logger.error(f"Error creating record in table {self.table_name}: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    async def update(self, *, id: IdentifierType, obj_in: UpdateSchemaType) -> Optional[ModelType]:
        """Update a record with proper handling of optional fields."""
        try:
            # Ensure id is a valid UUID string
            id_str = ensure_uuid(id)
            logger.debug(f"Updating record with ID: {id_str} in table {self.table_name}")
            
            # Use exclude_unset=True for partial updates and exclude None values
            update_data = obj_in.dict(exclude_unset=True, exclude_none=True, by_alias=False)

            if not update_data:
                # If there's nothing to update, return the existing object
                logger.debug(f"No fields to update for record {id_str}")
                return await self.get_by_id(id)

            # Serialize data for database
            update_data = self._serialize_data_for_db(update_data)

            # Step 1: Update the record
            query = self.db.table(self.table_name).update(update_data).eq("id", id_str)
            await self._execute_query(query)

            # Step 2: Fetch the updated record
            logger.debug(f"Record updated, fetching updated record with ID: {id_str}")
            return await self.get_by_id(id)
        except Exception as e:
            logger.error(f"Error updating record with ID {id} in table {self.table_name}: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    async def delete(self, *, id: IdentifierType) -> Optional[ModelType]:
        """Delete a record and return the deleted object if successful."""
        try:
            # Ensure id is a valid UUID string
            id_str = ensure_uuid(id)
            logger.debug(f"Deleting record with ID: {id_str} from table {self.table_name}")
            
            # Step 1: Get the object before deletion
            obj = await self.get_by_id(id)
            
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
            logger.error(f"Error deleting record with ID {id} from table {self.table_name}: {str(e)}")
            logger.error(traceback.format_exc())
            raise