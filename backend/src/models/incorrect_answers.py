# backend/src/models/incorrect_answers.py
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from .base_schema import BaseCreateSchema, BaseUpdateSchema


class IncorrectAnswers(BaseModel):
    """
    Model representing incorrect answer options for a question.
    
    Attributes:
        id: Unique identifier for this set of incorrect answers
        incorrect_answers: List of incorrect answer options
        question_id: Reference to the question these answers belong to
        created_at: When this record was created
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    incorrect_answers: List[str]
    question_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True  # Updated from orm_mode = True


class IncorrectAnswersCreate(BaseCreateSchema):
    """Schema for creating incorrect answers for a question."""
    incorrect_answers: List[str]
    question_id: str


class IncorrectAnswersUpdate(BaseUpdateSchema):
    """Schema for updating incorrect answers for a question."""
    incorrect_answers: Optional[List[str]] = None