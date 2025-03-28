from typing import List, Dict, Any, Optional
from models.category import Category, CreatorType
from repositories.base_repository import BaseRepository
import uuid

class CategoryRepository(BaseRepository[Category]):
    """
    Repository for managing categories in the database
    """
    def __init__(self, supabase_client):
        self.client = supabase_client
        self.categories_table = "categories"
    
    async def create(self, category: Category) -> Category:
        """Create a single category"""
        response = (
            self.client
            .table(self.categories_table)
            .insert(category.to_dict())
            .execute()
        )
        
        if response.data:
            category.id = response.data[0]["id"]
        
        return category
    
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
    
    async def bulk_create(self, categories: List[Category]) -> List[Category]:
        """Create multiple categories"""
        category_dicts = [c.to_dict() for c in categories]
        
        response = (
            self.client
            .table(self.categories_table)
            .insert(category_dicts)
            .execute()
        )
        
        for idx, data in enumerate(response.data):
            categories[idx].id = data["id"]
        
        return categories
    
    async def get_by_id(self, id: str) -> Optional[Category]:
        """Get category by ID"""
        response = (
            self.client
            .table(self.categories_table)
            .select("*")
            .eq("id", id)
            .execute()
        )
        
        if response.data:
            return Category.from_dict(response.data[0])
        
        return None
    
    async def get_by_name(self, name: str) -> Optional[Category]:
        """Get category by name"""
        if not name or not name.strip():
            return None
            
        sanitized_name = name.strip()
        
        response = (
            self.client
            .table(self.categories_table)
            .select("*")
            .eq("name", sanitized_name)
            .execute()
        )
        
        if response.data:
            return Category.from_dict(response.data[0])
        
        return None
    
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
    
    async def find(self, filter_params: Dict[str, Any], limit: int = 100) -> List[Category]:
        """Find categories matching criteria"""
        query = self.client.table(self.categories_table).select("*")
        
        for key, value in filter_params.items():
            query = query.eq(key, value)
        
        response = query.limit(limit).execute()
        
        return [Category.from_dict(data) for data in response.data]
    
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Category]:
        """Update a category"""
        response = (
            self.client
            .table(self.categories_table)
            .update(data)
            .eq("id", id)
            .execute()
        )
        
        if response.data:
            return Category.from_dict(response.data[0])
        
        return None
    
    async def increment_play_count(self, id: str) -> Optional[Category]:
        """Increment the play count for a category"""
        # First, get the current category to get the play count
        category = await self.get_by_id(id)
        if not category:
            return None
        
        # Increment the play count
        updated_data = {"play_count": category.play_count + 1}
        return await self.update(id, updated_data)
    
    async def delete(self, id: str) -> bool:
        """Delete a category"""
        response = (
            self.client
            .table(self.categories_table)
            .delete()
            .eq("id", id)
            .execute()
        )
        
        return len(response.data) > 0
    
    async def get_all_categories(self) -> List[Category]:
        """Get all categories"""
        response = (
            self.client
            .table(self.categories_table)
            .select("*")
            .execute()
        )
        
        return [Category.from_dict(data) for data in response.data]
    
    async def get_popular_categories(self, limit: int = 10) -> List[Category]:
        """Get most popular categories based on play count"""
        response = (
            self.client
            .table(self.categories_table)
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
            .table(self.categories_table)
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