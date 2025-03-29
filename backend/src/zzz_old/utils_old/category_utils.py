import logging
from typing import Optional, Dict, List, Any
import asyncio

from repositories.category_repository import CategoryRepository
from models.category import Category, CreatorType
from utils.cache_manager import CATEGORY_CACHE

# Configure logger
logger = logging.getLogger(__name__)

class CategoryUtils:
    """
    Utility class for centralizing category operations
    
    This class provides standardized methods for category resolution, 
    creation, and caching to ensure consistent behavior across all services.
    """
    
    def __init__(self, category_repository: Optional[CategoryRepository] = None):
        """
        Initialize with optional category repository
        
        Args:
            category_repository (CategoryRepository, optional): Repository for category operations
        """
        self.repository = category_repository
        
        # Cache for category data
        self.id_to_name_cache = {}
        self.name_to_id_cache = {}
    
    async def ensure_repository(self, supabase_client=None) -> CategoryRepository:
        """
        Ensure repository is initialized
        
        Args:
            supabase_client: Optional Supabase client
            
        Returns:
            CategoryRepository: Repository instance
        """
        if self.repository:
            return self.repository
            
        if supabase_client:
            self.repository = CategoryRepository(supabase_client)
            return self.repository
            
        # Try to create without client - may not work depending on implementation
        try:
            from repositories.category_repository import CategoryRepository
            self.repository = CategoryRepository(None)  # This may fail
            return self.repository
        except Exception as e:
            logger.error(f"Failed to create category repository: {e}")
            raise ValueError("Category repository not available")
    
    async def get_category_by_id(self, category_id: str) -> Optional[Category]:
        """
        Get category by ID with caching
        
        Args:
            category_id (str): Category ID
            
        Returns:
            Optional[Category]: Category if found
        """
        # Check cache first
        cache_key = f"category_id:{category_id}"
        cached_category = CATEGORY_CACHE.get(cache_key)
        if cached_category:
            return cached_category
            
        # Not in cache, fetch from repository
        try:
            repository = await self.ensure_repository()
            category = await repository.get_by_id(category_id)
            
            if category:
                # Update caches
                CATEGORY_CACHE.set(cache_key, category)
                id_name_key = f"id_to_name:{category_id}"
                CATEGORY_CACHE.set(id_name_key, category.name)
                name_id_key = f"name_to_id:{category.name.lower()}"
                CATEGORY_CACHE.set(name_id_key, category.id)
                
                # Also update local caches
                self.id_to_name_cache[category_id] = category.name
                self.name_to_id_cache[category.name.lower()] = category.id
                
            return category
            
        except Exception as e:
            logger.error(f"Error getting category by ID {category_id}: {e}")
            return None
    
    async def get_category_by_name(self, name: str) -> Optional[Category]:
        """
        Get category by name with caching
        
        Args:
            name (str): Category name
            
        Returns:
            Optional[Category]: Category if found
        """
        if not name:
            return None
            
        # Normalize name
        normalized_name = name.strip()
        
        # Check cache first
        cache_key = f"category_name:{normalized_name}"
        cached_category = CATEGORY_CACHE.get(cache_key)
        if cached_category:
            return cached_category
            
        # Check ID cache
        name_id_key = f"name_to_id:{normalized_name.lower()}"
        cached_id = CATEGORY_CACHE.get(name_id_key)
        if cached_id:
            return await self.get_category_by_id(cached_id)
            
        # Not in cache, fetch from repository
        try:
            repository = await self.ensure_repository()
            category = await repository.get_by_name(normalized_name)
            
            if category:
                # Update caches
                CATEGORY_CACHE.set(cache_key, category)
                id_name_key = f"id_to_name:{category.id}"
                CATEGORY_CACHE.set(id_name_key, category.name)
                name_id_key = f"name_to_id:{category.name.lower()}"
                CATEGORY_CACHE.set(name_id_key, category.id)
                
                # Also update local caches
                self.id_to_name_cache[category.id] = category.name
                self.name_to_id_cache[category.name.lower()] = category.id
                
            return category
            
        except Exception as e:
            logger.error(f"Error getting category by name '{normalized_name}': {e}")
            return None
    
    async def get_or_create_category(
        self, 
        name: str, 
        creator_type: CreatorType = CreatorType.SYSTEM
    ) -> Optional[Category]:
        """
        Get category by name or create if not exists
        
        Args:
            name (str): Category name
            creator_type (CreatorType): Creator type for new categories
            
        Returns:
            Optional[Category]: Category
        """
        if not name:
            return None
            
        # Normalize name
        normalized_name = name.strip()
        
        # Try to get existing category
        category = await self.get_category_by_name(normalized_name)
        if category:
            return category
            
        # Create new category
        try:
            repository = await self.ensure_repository()
            category = await repository.create_category_by_name(normalized_name, creator_type)
            
            if category:
                # Update caches
                cache_key = f"category_name:{normalized_name}"
                CATEGORY_CACHE.set(cache_key, category)
                id_name_key = f"id_to_name:{category.id}"
                CATEGORY_CACHE.set(id_name_key, category.name)
                name_id_key = f"name_to_id:{category.name.lower()}"
                CATEGORY_CACHE.set(name_id_key, category.id)
                
                # Also update local caches
                self.id_to_name_cache[category.id] = category.name
                self.name_to_id_cache[category.name.lower()] = category.id
                
            return category
            
        except Exception as e:
            logger.error(f"Error creating category '{normalized_name}': {e}")
            return None
    
    async def resolve_category_id(self, category_name_or_id: str) -> Optional[str]:
        """
        Resolve category ID from name or ID
        
        Args:
            category_name_or_id (str): Category name or ID
            
        Returns:
            Optional[str]: Category ID
        """
        if not category_name_or_id:
            return None
            
        # If it looks like a UUID, treat as ID
        if isinstance(category_name_or_id, str) and '-' in category_name_or_id:
            # Verify it's a valid category ID
            category = await self.get_category_by_id(category_name_or_id)
            return category_name_or_id if category else None
            
        # Treat as name
        normalized_name = category_name_or_id.strip()
        
        # Check cache
        name_id_key = f"name_to_id:{normalized_name.lower()}"
        cached_id = CATEGORY_CACHE.get(name_id_key)
        if cached_id:
            return cached_id
            
        # Not in cache, try to get or create
        category = await self.get_or_create_category(normalized_name)
        return category.id if category else None
    
    async def resolve_category_name(self, category_id_or_name: str) -> Optional[str]:
        """
        Resolve category name from ID or name
        
        Args:
            category_id_or_name (str): Category ID or name
            
        Returns:
            Optional[str]: Category name
        """
        if not category_id_or_name:
            return None
            
        # If it doesn't look like a UUID, treat as name
        if not isinstance(category_id_or_name, str) or '-' not in category_id_or_name:
            return category_id_or_name.strip()
            
        # Check cache
        id_name_key = f"id_to_name:{category_id_or_name}"
        cached_name = CATEGORY_CACHE.get(id_name_key)
        if cached_name:
            return cached_name
            
        # Not in cache, try to get
        category = await self.get_category_by_id(category_id_or_name)
        return category.name if category else category_id_or_name
    
    async def get_all_categories(self) -> List[Category]:
        """
        Get all categories
        
        Returns:
            List[Category]: All categories
        """
        try:
            repository = await self.ensure_repository()
            categories = await repository.get_all_categories()
            
            # Update caches
            for category in categories:
                cache_key = f"category_name:{category.name}"
                CATEGORY_CACHE.set(cache_key, category)
                id_name_key = f"id_to_name:{category.id}"
                CATEGORY_CACHE.set(id_name_key, category.name)
                name_id_key = f"name_to_id:{category.name.lower()}"
                CATEGORY_CACHE.set(name_id_key, category.id)
                
                # Also update local caches
                self.id_to_name_cache[category.id] = category.name
                self.name_to_id_cache[category.name.lower()] = category.id
                
            return categories
            
        except Exception as e:
            logger.error(f"Error getting all categories: {e}")
            return []
    
    async def get_popular_categories(self, limit: int = 10) -> List[Category]:
        """
        Get popular categories
        
        Args:
            limit (int): Maximum number of categories
            
        Returns:
            List[Category]: Popular categories
        """
        try:
            repository = await self.ensure_repository()
            categories = await repository.get_popular_categories(limit)
            
            # Update caches
            for category in categories:
                cache_key = f"category_name:{category.name}"
                CATEGORY_CACHE.set(cache_key, category)
                id_name_key = f"id_to_name:{category.id}"
                CATEGORY_CACHE.set(id_name_key, category.name)
                name_id_key = f"name_to_id:{category.name.lower()}"
                CATEGORY_CACHE.set(name_id_key, category.id)
                
                # Also update local caches
                self.id_to_name_cache[category.id] = category.name
                self.name_to_id_cache[category.name.lower()] = category.id
                
            return categories
            
        except Exception as e:
            logger.error(f"Error getting popular categories: {e}")
            return []
    
    def clear_cache(self):
        """Clear all category caches"""
        self.id_to_name_cache.clear()
        self.name_to_id_cache.clear()
        # Clear global cache keys related to categories
        for key in list(CATEGORY_CACHE.cache.keys()):
            if key.startswith(("category_", "id_to_name:", "name_to_id:")):
                CATEGORY_CACHE.invalidate(key)


# Create a singleton instance for global use
category_utils = CategoryUtils()