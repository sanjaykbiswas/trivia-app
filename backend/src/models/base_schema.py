# backend/src/models/base_schema.py
from pydantic import BaseModel
from typing import TypeVar, Generic, Type

ModelType = TypeVar('ModelType', bound=BaseModel)

class BaseCreateSchema(BaseModel):
    """Base schema for creating new models."""
    class Config:
        orm_mode = True

class BaseUpdateSchema(BaseModel):
    """Base schema for updating existing models."""
    class Config:
        orm_mode = True
        # Allow partial updates
        validate_assignment = True
        extra = "ignore"