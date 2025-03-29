# backend/src/models/user.py
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class User(BaseModel):
    """
    Model representing a user of the trivia application.
    
    Attributes:
        id: Unique identifier for the user
        displayname: Optional display name for the user
        email: Optional email address for the user
        is_temporary: Whether this is a temporary user account
        auth_provider: Optional authentication provider (e.g., 'google', 'facebook')
        auth_id: Optional identifier from the authentication provider
        created_at: When this user account was created
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    displayname: Optional[str] = None
    email: Optional[EmailStr] = None
    is_temporary: bool
    auth_provider: Optional[str] = None
    auth_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        orm_mode = True