import logging
from typing import Optional, Type, TypeVar, Any, Dict, List
import functools
import asyncio

from repositories.base_repository import BaseRepository
from repositories.category_repository import CategoryRepository

# Configure logger
logger = logging.getLogger(__name__)

# TypeVar for generic repository types
T = TypeVar('T', bound=BaseRepository)

class ServiceBase:
    """
    Base class for all service classes providing common functionality
    
    This class provides standard methods for repository access, error handling,
    and other common operations required by multiple services.
    """
    
    def __init__(
        self, 
        repository: Optional[BaseRepository] = None,
        category_repository: Optional[CategoryRepository] = None, 
        supabase_client: Any = None
    ):
        """
        Initialize service with optional repositories
        
        Args:
            repository (BaseRepository, optional): Primary repository for the service
            category_repository (CategoryRepository, optional): Repository for category operations
            supabase_client (Any, optional): Supabase client for database operations
        """
        self.repository = repository
        self.category_repository = category_repository
        self.supabase_client = supabase_client
        
        # For caching common data
        self._category_id_name_cache = {}
    
    async def get_repository(self, repo_class: Type[T] = None) -> Optional[T]:
        """
        Get the primary repository, creating it if necessary
        
        Args:
            repo_class (Type[T], optional): Repository class to instantiate if needed
            
        Returns:
            Optional[T]: Repository instance or None if cannot be created
        """
        if self.repository:
            return self.repository
            
        if repo_class and self.supabase_client:
            try:
                self.repository = repo_class(self.supabase_client)
                return self.repository
            except Exception as e:
                logger.error(f"Error creating repository: {e}")
        
        return None
    
    async def get_category_repository(self) -> Optional[CategoryRepository]:
        """
        Get the category repository, creating it if necessary
        
        Returns:
            Optional[CategoryRepository]: Category repository or None if cannot be created
        """
        if self.category_repository:
            return self.category_repository
            
        # Check if primary repository has a category_repository
        if hasattr(self.repository, 'category_repository') and self.repository.category_repository:
            self.category_repository = self.repository.category_repository
            return self.category_repository
            
        # Try to create a new repository
        if self.supabase_client:
            try:
                from repositories.category_repository import CategoryRepository
                self.category_repository = CategoryRepository(self.supabase_client)
                return self.category_repository
            except Exception as e:
                logger.error(f"Error creating category repository: {e}")
        
        return None
    
    async def resolve_category_id(self, category_name: str) -> Optional[str]:
        """
        Resolve a category ID from name, creating if necessary
        
        Args:
            category_name (str): Category name to resolve
            
        Returns:
            Optional[str]: Category ID or None if cannot be resolved
        """
        if not category_name:
            return None
        
        # Look up or create the category
        try:
            category_repo = await self.get_category_repository()
            if not category_repo:
                logger.warning(f"No category repository available to resolve '{category_name}'")
                return None
                
            category = await category_repo.get_or_create_by_name(category_name)
            if category:
                # Store in cache
                self._category_id_name_cache[category.id] = category.name
                return category.id
                
            return None
        except Exception as e:
            logger.error(f"Error resolving category ID for name '{category_name}': {e}")
            return None
    
    async def resolve_category_name(self, category_id: str) -> str:
        """
        Resolve a category name from ID
        
        Args:
            category_id (str): Category ID to look up
            
        Returns:
            str: Category name or the ID if not found
        """
        # Check if it looks like a UUID
        if not category_id or not isinstance(category_id, str) or '-' not in category_id:
            return category_id  # Not an ID, return as is
            
        # Check cache first
        if category_id in self._category_id_name_cache:
            return self._category_id_name_cache[category_id]
            
        try:
            # Look up in database
            category_repo = await self.get_category_repository()
            if not category_repo:
                return category_id
                
            category = await category_repo.get_by_id(category_id)
            
            if category:
                # Store in cache
                self._category_id_name_cache[category_id] = category.name
                return category.name
                
            return category_id  # Not found, return ID as fallback
        except Exception as e:
            logger.error(f"Error resolving category name for ID {category_id}: {e}")
            return category_id  # Return ID on error

    @staticmethod
    def catch_exceptions(func):
        """
        Decorator to catch and log exceptions in service methods
        
        Example usage:
            @ServiceBase.catch_exceptions
            async def some_method(self):
                # method implementation
        """
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                # Re-raise for higher-level handling
                raise
        return wrapper