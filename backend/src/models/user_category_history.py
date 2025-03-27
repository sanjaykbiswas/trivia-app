from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

@dataclass
class UserCategoryHistory:
    """
    Data model for tracking categories users have played
    """
    user_id: str
    category: str
    play_count: int = 1
    id: Optional[str] = None
    last_played_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self):
        """Convert to dictionary for database storage"""
        return {
            "user_id": self.user_id,
            "category": self.category,
            "play_count": self.play_count,
            "last_played_at": self.last_played_at.isoformat(),
            **({"id": self.id} if self.id else {})
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create UserCategoryHistory from dictionary"""
        if "last_played_at" in data and isinstance(data["last_played_at"], str):
            data["last_played_at"] = datetime.fromisoformat(data["last_played_at"])
        return cls(**data)