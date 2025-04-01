# backend/src/models/game_participant.py
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from .base_schema import BaseCreateSchema, BaseUpdateSchema

class GameParticipant(BaseModel):
    """
    Model representing a participant in a game session.
    
    Attributes:
        id: Unique identifier for this participant entry
        game_session_id: ID of the game session
        user_id: ID of the user participating
        display_name: Display name for this participant
        score: Current score in the game
        is_host: Whether this participant is the host of the game
        joined_at: When the participant joined the game
        last_activity: Last activity timestamp
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_session_id: str
    user_id: str
    display_name: str
    score: int = 0
    is_host: bool = False
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True

class GameParticipantCreate(BaseCreateSchema):
    """Schema for creating a new game participant."""
    game_session_id: str
    user_id: str
    display_name: str
    is_host: Optional[bool] = False

class GameParticipantUpdate(BaseUpdateSchema):
    """Schema for updating an existing game participant."""
    score: Optional[int] = None
    last_activity: Optional[datetime] = Field(default_factory=datetime.utcnow)