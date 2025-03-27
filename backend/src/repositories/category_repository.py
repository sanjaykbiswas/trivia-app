from typing import List, Dict, Any, Optional
from models.category import Category
from repositories.base_repository import BaseRepository

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
        response = (
            self.client
            .table(self.categories_table)
            .select("*")
            .eq("name", name)
            .execute()
        )
        
        if response.data:
            return Category.from_dict(response.data[0])
        
        return None
    
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