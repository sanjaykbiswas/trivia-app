# backend/src/models/pack.py
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


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
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    description: Optional[str] = None
    price: float
    pack_group_id: Optional[List[uuid.UUID]] = None
    creator_type: CreatorType
    correct_answer_rate: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        orm_mode = True