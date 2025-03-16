from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

@dataclass
class Question:
    """
    Data model for trivia questions
    """
    content: str
    category: str
    difficulty: Optional[str] = None  # Possible values: "Easy", "Medium", "Hard", "Expert", "Master"
    user: str = "system"  # Default to 'system' if no user is specified
    id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self):
        """Convert to dictionary for database storage"""
        return {
            "content": self.content,
            "category": self.category,
            "difficulty": self.difficulty,
            "user": self.user,
            "created_at": self.created_at.isoformat(),
            **({"id": self.id} if self.id else {})
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create Question from dictionary"""
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)