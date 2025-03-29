# backend/src/models/user_question_history.py
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class UserQuestionHistory(BaseModel):
    """
    Model representing a user's history with a specific question.
    
    Attributes:
        id: Unique identifier for this history entry
        user_id: Reference to the user
        question_id: Reference to the question
        correct: Whether the user answered correctly
        incorrect_answer_selected: Index of the incorrect answer selected (if any)
        created_at: When this record was created
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID
    question_id: uuid.UUID
    correct: bool
    incorrect_answer_selected: Optional[int] = None  # None when answered correctly
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        orm_mode = True