from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

@dataclass
class Answer:
    """
    Data model for trivia answers
    """
    question_id: str
    correct_answer: str
    incorrect_answers: List[str]
    id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self):
        """Convert to dictionary for database storage"""
        return {
            "question_id": self.question_id,
            "correct_answer": self.correct_answer,
            "incorrect_answers": self.incorrect_answers,
            "created_at": self.created_at.isoformat(),
            **({"id": self.id} if self.id else {})
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create Answer from dictionary"""
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)