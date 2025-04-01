# backend/src/api/schemas/user.py
from typing import Optional
from pydantic import BaseModel, EmailStr, Field # Remove field_serializer import
from datetime import datetime # Import datetime

class UserCreateRequest(BaseModel):
    """Request schema for creating a new user."""
    displayname: Optional[str] = Field(None, description="Display name for the user")
    email: Optional[EmailStr] = Field(None, description="Email address")
    is_temporary: bool = Field(False, description="Whether this is a temporary user account")
    auth_provider: Optional[str] = Field(None, description="Authentication provider (e.g., 'google', 'facebook')")
    auth_id: Optional[str] = Field(None, description="Identifier from the authentication provider")

class UserResponse(BaseModel):
    """Response schema for user data."""
    id: str
    displayname: Optional[str] = None
    email: Optional[str] = None
    is_temporary: bool
    auth_provider: Optional[str] = None
    created_at: datetime # <<< CHANGE THIS LINE back to datetime

    # Remove the custom serializer
    # @field_serializer('created_at', when_used='json')
    # def serialize_dt(self, dt: datetime):
    #     ... (removed) ...

    class Config:
        from_attributes = True # Use from_attributes for Pydantic v2

class UserUpdateRequest(BaseModel):
    """Request schema for updating an existing user."""
    displayname: Optional[str] = Field(None, description="New display name")
    email: Optional[EmailStr] = Field(None, description="New email address")
    is_temporary: Optional[bool] = Field(None, description="New temporary status")
    auth_provider: Optional[str] = Field(None, description="New authentication provider")
    auth_id: Optional[str] = Field(None, description="New authentication ID")

class UserLoginRequest(BaseModel):
    """Request schema for user login by email."""
    email: EmailStr = Field(..., description="Email address for login")
    password: str = Field(..., description="Password for login")

class UserAuthRequest(BaseModel):
    """Request schema for third-party authentication."""
    auth_provider: str = Field(..., description="Authentication provider (e.g., 'google', 'facebook')")
    auth_id: str = Field(..., description="Identifier from the authentication provider")
    email: Optional[EmailStr] = Field(None, description="Email address from the authentication provider")
    displayname: Optional[str] = Field(None, description="Display name from the authentication provider")

class UserConvertRequest(BaseModel):
    """Request schema for converting a temporary user to a permanent one."""
    displayname: str = Field(..., description="Display name for the user")
    email: Optional[EmailStr] = Field(None, description="Email address")
    auth_provider: Optional[str] = Field(None, description="Authentication provider")
    auth_id: Optional[str] = Field(None, description="Authentication ID")