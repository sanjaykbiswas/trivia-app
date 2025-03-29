from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from enum import Enum


class AuthProvider(str, Enum):
    EMAIL = "email"
    GOOGLE = "google"
    APPLE = "apple"
    NONE = "none"  # For temporary users


@dataclass
class User:
    """
    Data model for users
    """
    username: str
    is_temporary: bool = True
    auth_provider: AuthProvider = AuthProvider.NONE
    auth_id: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self):
        """Convert to dictionary for database storage"""
        return {
            "username": self.username,
            "is_temporary": self.is_temporary,
            "auth_provider": self.auth_provider.value,
            "auth_id": self.auth_id,
            "email": self.email,
            "avatar_url": self.avatar_url,
            "created_at": self.created_at.isoformat(),
            **({"id": self.id} if self.id else {})
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create User from dictionary"""
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        
        # Handle auth_provider as enum
        if "auth_provider" in data and isinstance(data["auth_provider"], str):
            data["auth_provider"] = AuthProvider(data["auth_provider"])
            
        return cls(**data)