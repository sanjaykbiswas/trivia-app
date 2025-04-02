# backend/src/models/pack.py
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any # Added Dict, Any
from pydantic import BaseModel, Field

from .base_schema import BaseCreateSchema, BaseUpdateSchema


class CreatorType(str, Enum):
    """Enum for types of pack creators"""
    SYSTEM = "system"
    USER = "user"


class Pack(BaseModel):
    """
    Model representing a pack of questions.

    Attributes:
        id: Unique identifier for the pack
        name: Name of the pack
        description: Optional description of the pack contents
        price: Price of the pack (could be 0 for free packs)
        pack_group_id: Optional list of PackGroup IDs this pack belongs to.
        creator_type: Whether this pack was created by the system or a user
        correct_answer_rate: Average rate of correct answers for this pack's questions
        created_at: When this pack was created
        seed_questions: Optional dictionary of seed questions and answers
        custom_difficulty_description: Optional dictionary of custom difficulty descriptions
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    price: float
    pack_group_id: Optional[List[str]] = None
    creator_type: CreatorType
    correct_answer_rate: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # --- ADDED FIELDS ---
    seed_questions: Dict[str, str] = Field(default_factory=dict)
    custom_difficulty_description: Dict[str, Any] = Field(default_factory=dict)
    # --- END ADDED FIELDS ---

    class Config:
        from_attributes = True


class PackCreate(BaseCreateSchema):
    """Schema for creating a new pack."""
    name: str
    description: Optional[str] = None
    price: float
    pack_group_id: Optional[List[str]] = None
    creator_type: CreatorType
    correct_answer_rate: Optional[float] = None
    # --- ADDED FIELDS (Optional on create) ---
    seed_questions: Optional[Dict[str, str]] = None
    custom_difficulty_description: Optional[Dict[str, Any]] = None
    # --- END ADDED FIELDS ---


class PackUpdate(BaseUpdateSchema):
    """Schema for updating an existing pack."""
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    pack_group_id: Optional[List[str]] = None
    creator_type: Optional[CreatorType] = None
    correct_answer_rate: Optional[float] = None
    # --- ADDED FIELDS (Optional on update) ---
    seed_questions: Optional[Dict[str, str]] = None
    custom_difficulty_description: Optional[Dict[str, Any]] = None
    # --- END ADDED FIELDS ---