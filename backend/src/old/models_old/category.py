from dataclasses import dataclass, field
from typing import Optional, Literal
from datetime import datetime
from enum import Enum

class CreatorType(str, Enum):
    SYSTEM = "system"
    USER = "user"

@dataclass
class Category:
    """
    Data model for trivia categories
    """
    name: str
    play_count: int = 0
    price: float = 0.0
    creator: CreatorType = CreatorType.SYSTEM
    id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self):
        """Convert to dictionary for database storage"""
        return {
            "name": self.name,
            "play_count": self.play_count,
            "price": self.price,
            "creator": self.creator.value,
            "created_at": self.created_at.isoformat(),
            **({"id": self.id} if self.id else {})
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create Category from dictionary"""
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        
        # Handle creator as enum
        if "creator" in data and isinstance(data["creator"], str):
            data["creator"] = CreatorType(data["creator"])
            
        return cls(**data)