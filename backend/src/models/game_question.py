# backend/src/models/game_question.py
import uuid
from datetime import datetime
from typing import Optional, Dict, List
from pydantic import BaseModel, Field

from .base_schema import BaseCreateSchema, BaseUpdateSchema

class GameQuestion(BaseModel):
    """
    Model representing a question in a game session.
    
    Attributes:
        id: Unique identifier for this game question
        game_session_id: ID of the game session
        question_id: ID of the original question
        question_index: Position of this question in the game sequence
        start_time: When this question was started
        end_time: When this question was completed
        participant_answers: Dictionary mapping participant IDs to their answer choices
        participant_scores: Dictionary mapping participant IDs to their scores for this question
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_session_id: str
    question_id: str
    question_index: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    participant_answers: Dict[str, str] = Field(default_factory=dict)
    participant_scores: Dict[str, int] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True

class GameQuestionCreate(BaseCreateSchema):
    """Schema for creating a new game question."""
    game_session_id: str
    question_id: str
    question_index: int

class GameQuestionUpdate(BaseUpdateSchema):
    """Schema for updating an existing game question."""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    participant_answers: Optional[Dict[str, str]] = None
    participant_scores: Optional[Dict[str, int]] = None