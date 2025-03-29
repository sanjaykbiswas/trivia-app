# backend/src/models/incorrect_answers.py
import uuid
from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


class IncorrectAnswers(BaseModel):
    """
    Model representing incorrect answer options for a question.
    
    Attributes:
        id: Unique identifier for this set of incorrect answers
        incorrect_answers: List of incorrect answer options
        question_id: Reference to the question these answers belong to
        created_at: When this record was created
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    incorrect_answers: List[str]
    question_id: uuid.UUID
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        orm_mode = True