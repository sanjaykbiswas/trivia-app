from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from pydantic import BaseModel, Field, validator
from services.category_service import CategoryService
from models.category import CreatorType
from utils.auth import get_current_user

# Pydantic models for API requests/responses
class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(0.0, ge=0.0)

class CategoryResponse(BaseModel):
    id: str
    name: str
    play_count: int
    price: float
    creator: str  # Use string for the enum value
    
    class Config:
        from_attributes = True  # For Pydantic v2 compatibility

class CategoryController:
    """
    Controller for category-related API endpoints
    """
    def __init__(self, category_service: CategoryService):
        """
        Initialize with the category service
        
        Args:
            category_service (CategoryService): Service for handling operations
        """
        self.category_service = category_service
        self.router = APIRouter(prefix="/categories", tags=["categories"])
        self._setup_routes()
    
    def _setup_routes(self):
        """Set up API routes"""
        # Public endpoints
        self.router.get("/", response_model=List[CategoryResponse])(self.get_categories)
        self.router.get("/popular", response_model=List[CategoryResponse])(self.get_popular_categories)
        self.router.get("/{category_id}", response_model=CategoryResponse)(self.get_category)
        
        # Authenticated endpoints
        self.router.post("/", response_model=CategoryResponse)(self.create_category)
        self.router.put("/{category_id}", response_model=CategoryResponse)(self.update_category)
        self.router.delete("/{category_id}", status_code=204)(self.delete_category)
        

    
    async def get_categories(
        self,
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100)
    ) -> List[CategoryResponse]:
        """
        Get all categories with pagination
        
        Args:
            skip (int): Number of records to skip
            limit (int): Maximum number of records to return
            
        Returns:
            List[CategoryResponse]: List of categories
        """
        categories = await self.category_service.get_all_categories()
        
        # Apply pagination
        paginated_categories = categories[skip:skip + limit]
        
        # Convert to response model format
        return [self._format_category_response(category) for category in paginated_categories]
    
    async def get_popular_categories(
        self,
        limit: int = Query(10, ge=1, le=50)
    ) -> List[CategoryResponse]:
        """
        Get most popular categories
        
        Args:
            limit (int): Maximum number of categories to return
            
        Returns:
            List[CategoryResponse]: List of popular categories
        """
        categories = await self.category_service.get_popular_categories(limit)
        
        # Convert to response model format
        return [self._format_category_response(category) for category in categories]
    
    async def get_category(self, category_id: str) -> CategoryResponse:
        """
        Get a single category by ID
        
        Args:
            category_id (str): Category ID
            
        Returns:
            CategoryResponse: Category details
        """
        category = await self.category_service.get_category_by_id(category_id)
        
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        return self._format_category_response(category)
    
    async def create_category(
        self,
        category_data: CategoryCreate,
        user_id: str = Depends(get_current_user)
    ) -> CategoryResponse:
        """
        Create a new category
        
        Args:
            category_data (CategoryCreate): Category data
            user_id (str): User ID from token
            
        Returns:
            CategoryResponse: Created category
        """
        try:
            category = await self.category_service.create_category(
                name=category_data.name,
                user_id=user_id,
                price=category_data.price
            )
            
            return self._format_category_response(category)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create category: {str(e)}")
    
    async def update_category(
        self,
        category_id: str,
        update_data: Dict[str, Any] = Body(...),
        user_id: str = Depends(get_current_user)
    ) -> CategoryResponse:
        """
        Update a category
        
        Args:
            category_id (str): Category ID
            update_data (Dict[str, Any]): Data to update
            user_id (str): User ID from token
            
        Returns:
            CategoryResponse: Updated category
        """
        # First, check if category exists
        category = await self.category_service.get_category_by_id(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        # In a real app, check permissions - only allow creator or admin to update
        # This is a simplified check
        # if category.creator == CreatorType.USER and str(category.creator_id) != user_id:
        #     raise HTTPException(status_code=403, detail="You don't have permission to update this category")
        
        try:
            updated_category = await self.category_service.update_category(category_id, update_data)
            
            if not updated_category:
                raise HTTPException(status_code=404, detail="Category not found")
            
            return self._format_category_response(updated_category)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update category: {str(e)}")
    
    async def delete_category(
        self,
        category_id: str,
        user_id: str = Depends(get_current_user)
    ):
        """
        Delete a category
        
        Args:
            category_id (str): Category ID
            user_id (str): User ID from token
        """
        # First, check if category exists
        category = await self.category_service.get_category_by_id(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        # In a real app, check permissions - only allow creator or admin to delete
        # This is a simplified check
        # if category.creator == CreatorType.USER and str(category.creator_id) != user_id:
        #     raise HTTPException(status_code=403, detail="You don't have permission to delete this category")
        
        success = await self.category_service.delete_category(category_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete category")
    

    
    def _format_category_response(self, category) -> CategoryResponse:
        """
        Format a category as an API response
        
        Args:
            category: Category model
            
        Returns:
            CategoryResponse: Formatted response
        """
        return CategoryResponse(
            id=category.id,
            name=category.name,
            play_count=category.play_count,
            price=category.price,
            creator=category.creator.value
        )