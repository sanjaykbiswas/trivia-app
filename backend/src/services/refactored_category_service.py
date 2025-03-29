from typing import List, Dict, Any, Optional
import logging
from models.category import Category, CreatorType
from services.service_base import ServiceBase
from utils.error_handling import async_handle_errors
from utils.category_utils import CategoryUtils

# Configure logger
logger = logging.getLogger(__name__)

class RefactoredCategoryService(ServiceBase):
    """
    Refactored service for managing trivia categories
    
    This service handles category creation, updates, and retrieval
    """
    def __init__(self, category_repository):
        """
        Initialize service with repository
        
        Args:
            category_repository: Repository for data access
        """
        super().__init__(category_repository)
        self.category_utils = CategoryUtils()
    
    @async_handle_errors
    async def create_category(
        self,
        name: str,
        user_id: Optional[str] = None,
        price: float = 0.0,
    ) -> Category:
        """
        Create a new category
        
        Args:
            name (str): Category name
            user_id (Optional[str]): ID of user creating the category (None for system)
            price (float): Price for premium categories (default: 0.0 for free)
            
        Returns:
            Category: Created category with ID
        """
        if not name or not name.strip():
            raise ValueError("Category name cannot be empty")
        
        # Clean the name
        name = name.strip()
        
        # Check if category already exists
        existing = await self.repository.get_by_name(name)
        if existing:
            logger.info(f"Category '{name}' already exists with ID: {existing.id}")
            return existing
            
        # Determine creator type - system if no user_id
        creator_type = CreatorType.USER if user_id else CreatorType.SYSTEM
        
        # If no user_id, use the system UUID
        if not user_id:
            user_id = "00000000-0000-0000-0000-000000000000"  # System UUID
        
        # Create category object
        category = Category(
            name=name,
            play_count=0,  # Initial play count is zero
            price=price,
            creator=creator_type
        )
        
        # Save to database using the base class method
        created_category = await self.repository.create(category)
        logger.info(f"Created category '{name}' with ID: {created_category.id}")
        
        return created_category
    
    @async_handle_errors
    async def get_category_by_id(self, category_id: str) -> Optional[Category]:
        """
        Get category by ID
        
        Args:
            category_id (str): Category ID
            
        Returns:
            Optional[Category]: Category if found
        """
        return await self.repository.get_by_id(category_id)
    
    @async_handle_errors
    async def get_category_by_name(self, name: str) -> Optional[Category]:
        """
        Get category by name
        
        Args:
            name (str): Category name
            
        Returns:
            Optional[Category]: Category if found
        """
        if not name or not name.strip():
            return None
            
        return await self.repository.get_by_name(name.strip())
    
    @async_handle_errors
    async def update_category(self, category_id: str, data: Dict[str, Any]) -> Optional[Category]:
        """
        Update category properties
        
        Args:
            category_id (str): Category ID
            data (Dict[str, Any]): Data to update
            
        Returns:
            Optional[Category]: Updated category if found
        """
        # Clean name if provided
        if "name" in data and data["name"]:
            data["name"] = data["name"].strip()
            
        # Check if the new name already exists
        if "name" in data and data["name"]:
            existing = await self.repository.get_by_name(data["name"])
            if existing and existing.id != category_id:
                logger.warning(f"Cannot update category: name '{data['name']}' already exists")
                raise ValueError(f"Category name '{data['name']}' already exists")
        
        return await self.repository.update(category_id, data)
    
    @async_handle_errors
    async def increment_play_count(self, category_id: str) -> Optional[Category]:
        """
        Increment the play count for a category
        
        Args:
            category_id (str): Category ID
            
        Returns:
            Optional[Category]: Updated category if found
        """
        return await self.repository.increment_play_count(category_id)
    
    @async_handle_errors
    async def get_all_categories(self) -> List[Category]:
        """
        Get all categories
        
        Returns:
            List[Category]: All categories
        """
        return await self.repository.get_all_categories()
    
    @async_handle_errors
    async def get_popular_categories(self, limit: int = 10) -> List[Category]:
        """
        Get most popular categories based on play count
        
        Args:
            limit (int): Maximum number of categories to return
            
        Returns:
            List[Category]: Popular categories
        """
        return await self.repository.get_popular_categories(limit)
    
    @async_handle_errors
    async def delete_category(self, category_id: str) -> bool:
        """
        Delete a category
        
        Args:
            category_id (str): Category ID
            
        Returns:
            bool: Success status
        """
        return await self.repository.delete(category_id)