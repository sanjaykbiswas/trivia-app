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
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    pack_id: str
    play_count: int
    last_played_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True  # Updated from orm_mode = True


class UserPackHistoryCreate(BaseCreateSchema):
    """Schema for creating a new user pack history entry."""
    user_id: str
    pack_id: str
    play_count: int
    last_played_at: Optional[datetime] = None


class UserPackHistoryUpdate(BaseUpdateSchema):
    """Schema for updating an existing user pack history entry."""
    play_count: Optional[int] = None
    last_played_at: Optional[datetime] = None