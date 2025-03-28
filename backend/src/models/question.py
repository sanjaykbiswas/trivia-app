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
    category_id: Optional[str] = None  # UUID as string for the category
    category_name: Optional[str] = None  # Used for in-memory reference only, not stored in DB
    difficulty: Optional[str] = None  # Possible values: "Easy", "Medium", "Hard", "Expert", "Master"
    modified_difficulty: Optional[str] = None  # Initially same as difficulty, can be modified later
    id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self):
        """Convert to dictionary for database storage"""
        # Only include fields that are in the database schema
        db_dict = {
            "content": self.content,
            "difficulty": self.difficulty,
            "modified_difficulty": self.modified_difficulty,
            "created_at": self.created_at.isoformat(),
        }
        
        # Add category_id if it exists - this is in the DB schema
        if self.category_id:
            db_dict["category_id"] = self.category_id
            
        # Add ID if it exists
        if self.id:
            db_dict["id"] = self.id
            
        # Remove None values to avoid database issues
        return {k: v for k, v in db_dict.items() if v is not None}
    
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