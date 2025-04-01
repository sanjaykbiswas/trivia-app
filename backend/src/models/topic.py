# backend/src/models/topic.py
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from .base_schema import BaseCreateSchema, BaseUpdateSchema

class Topic(BaseModel):
    """
    Model representing a single topic within a pack.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pack_id: str # Foreign key to packs table
    name: str
    custom_instruction: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True

class TopicCreate(BaseCreateSchema):
    """Schema for creating a new topic."""
    pack_id: str
    name: str
    custom_instruction: Optional[str] = None

class TopicUpdate(BaseUpdateSchema):
    """Schema for updating an existing topic."""
    name: Optional[str] = None # Usually you wouldn't change the name/pack_id
    custom_instruction: Optional[str] = None