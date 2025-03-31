# backend/src/models/pack_group.py
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from .base_schema import BaseCreateSchema, BaseUpdateSchema


class PackGroup(BaseModel):
    """
    Model representing a group of question packs.
    
    Attributes:
        id: Unique identifier for the pack group
        name: Name of the pack group
        created_at: When this pack group was created
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True  # Updated from orm_mode = True


class PackGroupCreate(BaseCreateSchema):
    """Schema for creating a new pack group."""
    name: str


class PackGroupUpdate(BaseUpdateSchema):
    """Schema for updating an existing pack group."""
    name: Optional[str] = None