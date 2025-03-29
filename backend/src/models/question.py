# backend/src/models/question.py
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, root_validator

from .base_schema import BaseCreateSchema, BaseUpdateSchema


class DifficultyLevel(str, Enum):
    """Enum for difficulty levels of questions"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class Question(BaseModel):
    """
    Model representing a trivia question.
    
    Attributes:
        id: Unique identifier for the question
        question: The actual trivia question text
        answer: The correct answer to the question
        pack_id: Reference to the pack this question belongs to
        difficulty_initial: The original difficulty rating when created
        difficulty_current: The current difficulty rating (may change over time)
        correct_answer_rate: Percentage of correct answers given by users
        created_at: When this question was created
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    question: str
    answer: str
    pack_id: uuid.UUID
    difficulty_initial: DifficultyLevel
    difficulty_current: Optional[DifficultyLevel] = None
    correct_answer_rate: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @root_validator(pre=True)
    def set_default_difficulty_current(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Default difficulty_current to difficulty_initial if not provided"""
        if 'difficulty_current' not in values or values['difficulty_current'] is None:
            if 'difficulty_initial' in values:
                values['difficulty_current'] = values['difficulty_initial']
        return values
    
    class Config:
        orm_mode = True


class QuestionCreate(BaseCreateSchema):
    """Schema for creating a new question."""
    question: str
    answer: str
    pack_id: uuid.UUID
    difficulty_initial: DifficultyLevel
    difficulty_current: Optional[DifficultyLevel] = None
    
    # Default values not required in creation schema
    correct_answer_rate: float = 0.0


class QuestionUpdate(BaseUpdateSchema):
    """Schema for updating an existing question."""
    question: Optional[str] = None
    answer: Optional[str] = None
    difficulty_current: Optional[DifficultyLevel] = None
    correct_answer_rate: Optional[float] = None