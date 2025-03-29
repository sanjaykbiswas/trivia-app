from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

@dataclass
class UserQuestionHistory:
    """
    Data model for tracking which questions users have seen
    """
    user_id: str
    question_id: str
    correct: bool
    answer_selected: Optional[int] = None
    id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self):
        """Convert to dictionary for database storage"""
        return {
            "user_id": self.user_id,
            "question_id": self.question_id,
            "correct": self.correct,
            "answer_selected": self.answer_selected,
            "created_at": self.created_at.isoformat(),
            **({"id": self.id} if self.id else {})
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create UserQuestionHistory from dictionary"""
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)