# backend/src/models/base_schema.py
from pydantic import BaseModel
from typing import TypeVar, Generic, Type

ModelType = TypeVar('ModelType', bound=BaseModel)

class BaseCreateSchema(BaseModel):
    """Base schema for creating new models."""
    class Config:
        from_attributes = True  # Was orm_mode = True in V1

class BaseUpdateSchema(BaseModel):
    """Base schema for updating existing models."""
    class Config:
        from_attributes = True  # Was orm_mode = True in V1
        # Allow partial updates
        validate_assignment = True
        extra = "ignore"