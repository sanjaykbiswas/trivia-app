import logging
from typing import List, Dict, Any, Optional, TypeVar, Generic, Type
import uuid
from abc import ABC
from datetime import datetime

from repositories.base_repository import BaseRepository

# Type variable for model objects
T = TypeVar('T')

# Configure logger
logger = logging.getLogger(__name__)

class BaseRepositoryImpl(BaseRepository[T], Generic[T]):
    """
    Base implementation of repository for database operations with Supabase
    
    This class implements the abstract BaseRepository with specific Supabase
    operations, providing a consistent pattern for all repositories.
    """
    
    def __init__(self, supabase_client, table_name: str, model_class: Type[T]):
        """
        Initialize with Supabase client, table name, and model class
        
        Args:
            supabase_client: Supabase client instance
            table_name (str): Database table name
            model_class (Type[T]): Model class for data conversion
        """
        self.client = supabase_client
        self.table_name = table_name
        self.model_class = model_class
    
    async def create(self, item: T) -> T:
        """
        Create a single item in the database
        
        Args:
            item (T): Item to create
            
        Returns:
            T: Created item with ID
        """
        # Convert to dictionary for database
        item_dict = item.to_dict() if hasattr(item, 'to_dict') else item
        
        response = (
            self.client
            .table(self.table_name)
            .insert(item_dict)
            .execute()
        )
        
        if response.data and len(response.data) > 0:
            # Set ID on original item
            if hasattr(item, 'id'):
                item.id = response.data[0]['id']
                
            return item
        else:
            logger.error(f"Failed to create item in {self.table_name}")
            return item
    
    async def bulk_create(self, items: List[T]) -> List[T]:
        """
        Create multiple items in the database
        
        Args:
            items (List[T]): Items to create
            
        Returns:
            List[T]: Created items with IDs
        """
        if not items:
            return []
            
        # Convert items to dictionaries
        item_dicts = []
        for item in items:
            if hasattr(item, 'to_dict'):
                item_dicts.append(item.to_dict())
            else:
                item_dicts.append(item)
        
        response = (
            self.client
            .table(self.table_name)
            .insert(item_dicts)
            .execute()
        )
        
        # Update original items with IDs
        if response.data:
            for i, data in enumerate(response.data):
                if i < len(items) and hasattr(items[i], 'id'):
                    items[i].id = data['id']
        
        return items
    
    async def get_by_id(self, id: str) -> Optional[T]:
        """
        Get item by ID
        
        Args:
            id (str): Item ID
            
        Returns:
            Optional[T]: Item if found, None otherwise
        """
        response = (
            self.client
            .table(self.table_name)
            .select("*")
            .eq("id", id)
            .execute()
        )
        
        if response.data and len(response.data) > 0:
            # Convert to model object if class provided
            if self.model_class and hasattr(self.model_class, 'from_dict'):
                return self.model_class.from_dict(response.data[0])
            return response.data[0]
        
        return None
    
    async def find(self, filter_params: Dict[str, Any], limit: int = 100) -> List[T]:
        """
        Find items matching criteria
        
        Args:
            filter_params (Dict[str, Any]): Filter parameters
            limit (int): Maximum items to return
            
        Returns:
            List[T]: Matching items
        """
        query = self.client.table(self.table_name).select("*")
        
        # Apply filters
        for key, value in filter_params.items():
            query = query.eq(key, value)
        
        response = query.limit(limit).execute()
        
        # Convert to model objects if class provided
        if self.model_class and hasattr(self.model_class, 'from_dict'):
            return [self.model_class.from_dict(data) for data in response.data]
        
        return response.data
    
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[T]:
        """
        Update an item
        
        Args:
            id (str): Item ID
            data (Dict[str, Any]): Data to update
            
        Returns:
            Optional[T]: Updated item if found
        """
        response = (
            self.client
            .table(self.table_name)
            .update(data)
            .eq("id", id)
            .execute()
        )
        
        if response.data and len(response.data) > 0:
            # Convert to model object if class provided
            if self.model_class and hasattr(self.model_class, 'from_dict'):
                return self.model_class.from_dict(response.data[0])
            return response.data[0]
        
        return None
    
    async def delete(self, id: str) -> bool:
        """
        Delete an item
        
        Args:
            id (str): Item ID
            
        Returns:
            bool: Success status
        """
        response = (
            self.client
            .table(self.table_name)
            .delete()
            .eq("id", id)
            .execute()
        )
        
        return len(response.data) > 0