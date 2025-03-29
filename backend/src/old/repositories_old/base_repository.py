from abc import ABC, abstractmethod
from typing import List, Any, Dict, Optional, TypeVar, Generic

T = TypeVar('T')  # Generic type for model objects

class BaseRepository(ABC, Generic[T]):
    """
    Abstract base repository defining common data operations
    All methods are async for consistent asynchronous operation
    """
    @abstractmethod
    async def create(self, item: T) -> T:
        """Create a single item"""
        pass
    
    @abstractmethod
    async def bulk_create(self, items: List[T]) -> List[T]:
        """Create multiple items"""
        pass
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[T]:
        """Get item by ID"""
        pass
    
    @abstractmethod
    async def find(self, filter_params: Dict[str, Any], limit: int = 100) -> List[T]:
        """Find items matching criteria"""
        pass
    
    @abstractmethod
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[T]:
        """Update an item"""
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete an item"""
        pass