# backend/src/models/question.py
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from uuid import UUID

@dataclass
class Question:
    """
    Data model for trivia questions
    """
    content: str
    category_id: str  # UUID as string for the category
    category_name: Optional[str] = None  # Optional name for backward compatibility
    difficulty: Optional[str] = None  # Possible values: "Easy", "Medium", "Hard", "Expert", "Master"
    modified_difficulty: Optional[str] = None  # Initially same as difficulty, can be modified later
    id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self):
        """Convert to dictionary for database storage"""
        return {
            "content": self.content,
            "category_id": self.category_id,
            "category_name": self.category_name,
            "difficulty": self.difficulty,
            "modified_difficulty": self.modified_difficulty,
            "created_at": self.created_at.isoformat(),
            **({"id": self.id} if self.id else {})
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create Question from dictionary"""
        # Handle created_at as ISO string
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        
        # Handle backward compatibility for category field
        if "category" in data and "category_id" not in data:
            # If we only have the old category field, store it in category_name
            data["category_name"] = data.pop("category")
            # Note: The caller should handle setting the proper category_id
        
        return cls(**data)