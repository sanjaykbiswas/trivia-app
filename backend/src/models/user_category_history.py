from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

@dataclass
class UserCategoryHistory:
    """
    Data model for tracking categories users have played
    """
    user_id: str
    category_id: str  # Changed from category string to category_id (UUID as string)
    category_name: Optional[str] = None  # Added for convenience/display
    play_count: int = 1
    id: Optional[str] = None
    last_played_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self):
        """Convert to dictionary for database storage"""
        data = {
            "user_id": self.user_id,
            "category_id": self.category_id,
            "play_count": self.play_count,
            "last_played_at": self.last_played_at.isoformat(),
        }
        
        if self.category_name is not None:
            data["category_name"] = self.category_name
            
        if self.id:
            data["id"] = self.id
            
        return data
    
    @classmethod
    def from_dict(cls, data):
        """Create UserCategoryHistory from dictionary"""
        # Handle last_played_at as ISO string
        if "last_played_at" in data and isinstance(data["last_played_at"], str):
            data["created_at"] = datetime.fromisoformat(data["last_played_at"])
            
        # Handle backward compatibility for old 'category' field
        if "category" in data and "category_id" not in data:
            # Store old category string in category_name for reference
            data["category_name"] = data.pop("category")
            # Note: The caller should handle setting the proper category_id
        
        return cls(**data)