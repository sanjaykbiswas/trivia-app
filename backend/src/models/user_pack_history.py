# backend/src/models/user_pack_history.py
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from .base_schema import BaseCreateSchema, BaseUpdateSchema


class UserPackHistory(BaseModel):
    """
    Model representing a user's history with a specific pack.
    
    Attributes:
        id: Unique identifier for this history entry
        user_id: Reference to the user
        pack_id: Reference to the pack
        play_count: Number of times the user has played this pack
        last_played_at: When the user last played this pack
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID
    pack_id: uuid.UUID
    play_count: int
    last_played_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        orm_mode = True


class UserPackHistoryCreate(BaseCreateSchema):
    """Schema for creating a new user pack history entry."""
    user_id: uuid.UUID
    pack_id: uuid.UUID
    play_count: int
    last_played_at: Optional[datetime] = None


class UserPackHistoryUpdate(BaseUpdateSchema):
    """Schema for updating an existing user pack history entry."""
    play_count: Optional[int] = None
    last_played_at: Optional[datetime] = None