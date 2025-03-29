# backend/src/repositories/base_repository.py
import uuid
from abc import ABC, abstractmethod
from typing import List, Optional, TypeVar, Generic, Type
from pydantic import BaseModel

# Define TypeVars for generic repository
ModelType = TypeVar('ModelType', bound=BaseModel)
CreateSchemaType = TypeVar('CreateSchemaType', bound=BaseModel)
UpdateSchemaType = TypeVar('UpdateSchemaType', bound=BaseModel)
IdentifierType = TypeVar('IdentifierType', bound=uuid.UUID) # Assuming UUID primary keys

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType, IdentifierType], ABC):
    """
    Abstract base class for data repositories.

    Defines the standard interface for CRUD operations with separate
    schema types for creation and update operations.
    """

    @abstractmethod
    async def get_by_id(self, id: IdentifierType) -> Optional[ModelType]:
        """Retrieve a single item by its unique identifier."""
        pass

    @abstractmethod
    async def get_all(self, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Retrieve multiple items, with optional pagination."""
        pass

    @abstractmethod
    async def create(self, *, obj_in: CreateSchemaType) -> ModelType:
        """Create a new item using the creation schema."""
        pass

    @abstractmethod
    async def update(self, *, id: IdentifierType, obj_in: UpdateSchemaType) -> Optional[ModelType]:
        """Update an existing item by its unique identifier using the update schema."""
        pass

    @abstractmethod
    async def delete(self, *, id: IdentifierType) -> Optional[ModelType]:
        """Delete an item by its unique identifier and return the deleted item if successful."""
        pass