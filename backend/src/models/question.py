# backend/src/models/question.py
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator

from .base_schema import BaseCreateSchema, BaseUpdateSchema


class DifficultyLevel(str, Enum):
    """Enum for difficulty levels of questions"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"
    MIXED = "mixed"  # Added MIXED difficulty level


class Question(BaseModel):
    """
    Model representing a trivia question.
    
    Attributes:
        id: Unique identifier for the question
        question: The actual trivia question text
        answer: The correct answer to the question
        pack_id: Reference to the pack this question belongs to
        pack_topics_item: Topic or subject area of the question
        difficulty_initial: The original difficulty rating when created (now optional)
        difficulty_current: The current difficulty rating (optional)
        correct_answer_rate: Percentage of correct answers given by users
        created_at: When this question was created
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str
    answer: str
    pack_id: str
    pack_topics_item: Optional[str] = None
    difficulty_initial: Optional[DifficultyLevel] = None
    difficulty_current: Optional[DifficultyLevel] = None
    correct_answer_rate: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Updated from root_validator to model_validator for Pydantic v2
    @model_validator(mode='before')
    @classmethod
    def set_default_difficulty_current(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Default difficulty_current to difficulty_initial if not provided,
        but only when difficulty_initial exists
        """
        if isinstance(data, dict):
            if 'difficulty_current' not in data or data['difficulty_current'] is None:
                if 'difficulty_initial' in data and data['difficulty_initial'] is not None:
                    data['difficulty_current'] = data['difficulty_initial']
        return data
    
    class Config:
        from_attributes = True  # Updated from orm_mode = True


class QuestionCreate(BaseCreateSchema):
    """Schema for creating a new question."""
    question: str
    answer: str
    pack_id: str
    pack_topics_item: Optional[str] = None
    difficulty_initial: Optional[DifficultyLevel] = None
    difficulty_current: Optional[DifficultyLevel] = None
    
    # Default values not required in creation schema
    correct_answer_rate: float = 0.0


class QuestionUpdate(BaseUpdateSchema):
    """Schema for updating an existing question."""
    question: Optional[str] = None
    answer: Optional[str] = None
    pack_topics_item: Optional[str] = None
    difficulty_initial: Optional[DifficultyLevel] = None
    difficulty_current: Optional[DifficultyLevel] = None
    correct_answer_rate: Optional[float] = None