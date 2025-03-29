# backend/src/repositories/category_repository.py
from typing import List, Dict, Any, Optional
from models.category import Category, CreatorType
from repositories.base_repository_impl import BaseRepositoryImpl
import uuid

class CategoryRepository(BaseRepositoryImpl[Category]):
    """
    Repository for managing categories in the database
    """
    def __init__(self, supabase_client):
        """Initialize with Supabase client"""
        super().__init__(supabase_client, "categories", Category)
    
    async def get_by_name(self, name: str) -> Optional[Category]:
        """Get category by name"""
        if not name or not name.strip():
            return None
            
        sanitized_name = name.strip()
        
        response = (
            self.client
            .table(self.table_name)
            .select("*")
            .eq("name", sanitized_name)
            .execute()
        )
        
        if response.data:
            return Category.from_dict(response.data[0])
        
        return None
    
    async def create_category_by_name(self, name: str, creator_type: CreatorType = CreatorType.SYSTEM) -> Category:
        """
        Create a new category using just the name
        
        Args:
            name (str): Category name to create
            creator_type (CreatorType): Type of creator (default: SYSTEM)
            
        Returns:
            Category: Created category with ID
        """
        # First check if category already exists
        existing = await self.get_by_name(name)
        if existing:
            return existing
            
        # Create new category
        new_category = Category(
            name=name,
            creator=creator_type
        )
        
        return await self.create(new_category)
    
    async def get_or_create_by_name(self, name: str) -> Category:
        """
        Get a category by name or create it if it doesn't exist
        
        Args:
            name (str): Category name
            
        Returns:
            Category: Existing or newly created category
        """
        existing = await self.get_by_name(name)
        if existing:
            return existing
            
        return await self.create_category_by_name(name)
    
    async def increment_play_count(self, id: str) -> Optional[Category]:
        """Increment the play count for a category"""
        # First, get the current category to get the play count
        category = await self.get_by_id(id)
        if not category:
            return None
        
        # Increment the play count
        updated_data = {"play_count": category.play_count + 1}
        return await self.update(id, updated_data)
    
    async def get_all_categories(self) -> List[Category]:
        """Get all categories"""
        response = (
            self.client
            .table(self.table_name)
            .select("*")
            .execute()
        )
        
        return [Category.from_dict(data) for data in response.data]
    
    async def get_popular_categories(self, limit: int = 10) -> List[Category]:
        """Get most popular categories based on play count"""
        response = (
            self.client
            .table(self.table_name)
            .select("*")
            .order("play_count", desc=True)
            .limit(limit)
            .execute()
        )
        
        return [Category.from_dict(data) for data in response.data]
        
    async def get_or_create_default_category(self) -> Category:
        """
        Get or create the default 'General Knowledge' category
        
        Returns:
            Category: Default category
        """
        default_name = "General Knowledge"
        default_category = await self.get_by_name(default_name)
        
        if default_category:
            return default_category
            
        # Create the default category
        return await self.create_category_by_name(default_name)
    
    async def search_categories(self, search_term: str, limit: int = 10) -> List[Category]:
        """
        Search for categories by name
        
        Args:
            search_term (str): Term to search for
            limit (int): Maximum results to return
            
        Returns:
            List[Category]: Matching categories
        """
        # Some database systems don't support LIKE queries directly
        # This is a simplified implementation
        response = (
            self.client
            .table(self.table_name)
            .select("*")
            .execute()
        )
        
        if not response.data:
            return []
            
        # Filter results on the client side
        search_term = search_term.lower()
        filtered_data = [
            data for data in response.data 
            if search_term in data.get("name", "").lower()
        ]
        
        # Apply limit
        filtered_data = filtered_data[:limit]
        
        return [Category.from_dict(data) for data in filtered_data]