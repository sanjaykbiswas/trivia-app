# backend/src/models/game_session.py
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field

from .base_schema import BaseCreateSchema, BaseUpdateSchema

class GameStatus(str, Enum):
    """Enum for the status of a game session"""
    PENDING = "pending"    # Game created but not started
    ACTIVE = "active"      # Game in progress
    COMPLETED = "completed"  # Game finished
    CANCELLED = "cancelled"  # Game cancelled

class GameSession(BaseModel):
    """
    Model representing a game session.
    
    Attributes:
        id: Unique identifier for the game session
        code: Unique code for joining the game
        host_user_id: ID of the user who created this game session
        pack_id: ID of the pack being used for this game
        status: Current status of the game
        max_participants: Maximum number of participants allowed
        question_count: Number of questions in the game
        time_limit_seconds: Time limit for answering each question (0 means no limit)
        current_question_index: Index of the current question being played
        created_at: When this game session was created
        updated_at: When this game session was last updated
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    host_user_id: str
    pack_id: str
    status: GameStatus = GameStatus.PENDING
    max_participants: int = 10
    question_count: int = 10
    time_limit_seconds: int = 0
    current_question_index: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True

class GameSessionCreate(BaseCreateSchema):
    """Schema for creating a new game session."""
    code: str
    host_user_id: str
    pack_id: str
    max_participants: Optional[int] = 10
    question_count: Optional[int] = 10
    time_limit_seconds: Optional[int] = 0
    status: Optional[GameStatus] = GameStatus.PENDING

class GameSessionUpdate(BaseUpdateSchema):
    """Schema for updating an existing game session."""
    status: Optional[GameStatus] = None
    current_question_index: Optional[int] = None
    max_participants: Optional[int] = None
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)