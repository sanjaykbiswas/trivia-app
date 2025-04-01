# backend/src/models/pack_creation_data.py
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any # Removed List from here as pack_topics is gone
from pydantic import BaseModel, Field

from .base_schema import BaseCreateSchema, BaseUpdateSchema


class PackCreationData(BaseModel):
    """
    Model representing metadata about pack creation.
    NOTE: pack_topics and custom_question_instructions have been removed.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pack_id: str
    creation_name: str
    is_pow: Optional[bool] = False
    pow_analysis: Optional[str] = None
    # pack_topics: List[str] # REMOVED
    custom_difficulty_description: Dict[str, Any] = Field(default_factory=dict)
    seed_questions: Dict[str, str] = Field(default_factory=dict)
    # custom_question_instructions: Optional[str] = None # REMOVED
    is_temporal: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class PackCreationDataCreate(BaseCreateSchema):
    """Schema for creating new pack creation metadata."""
    pack_id: str
    creation_name: str
    is_pow: Optional[bool] = False
    pow_analysis: Optional[str] = None
    # pack_topics: List[str] # REMOVED
    custom_difficulty_description: Dict[str, Any] = Field(default_factory=dict)
    seed_questions: Dict[str, str] = Field(default_factory=dict)
    # custom_question_instructions: Optional[str] = None # REMOVED
    is_temporal: bool = False


class PackCreationDataUpdate(BaseUpdateSchema):
    """Schema for updating existing pack creation metadata."""
    creation_name: Optional[str] = None
    is_pow: Optional[bool] = None
    pow_analysis: Optional[str] = None
    # pack_topics: Optional[List[str]] = None # REMOVED
    custom_difficulty_description: Optional[Dict[str, Any]] = None
    seed_questions: Optional[Dict[str, str]] = None
    # custom_question_instructions: Optional[str] = None # REMOVED
    is_temporal: Optional[bool] = None