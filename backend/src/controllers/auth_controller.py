from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, Field
from utils.auth import get_current_user
from typing import Dict, Optional
from services.user_service import UserService

class UserResponse(BaseModel):
    user_id: str

class TempUserRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)

class LinkIdentityRequest(BaseModel):
    temp_user_id: str
    auth_provider: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None

class AuthController:
    """
    Controller for authentication-related endpoints
    """
    def __init__(self, user_service=None):
        self.router = APIRouter(prefix="/auth", tags=["auth"])
        self.user_service = user_service
        self._setup_routes()
    
    def _setup_routes(self):
        """Set up API routes"""
        self.router.get("/me", response_model=UserResponse)(self.get_current_user)
        self.router.post("/temp-user", response_model=Dict)(self.create_temp_user)
        self.router.post("/link-identity", response_model=Dict)(self.link_identity)
    
    async def get_current_user(self, user_id: str = Depends(get_current_user)) -> UserResponse:
        """
        Get current authenticated user
        
        Args:
            user_id: User ID from token
        
        Returns:
            UserResponse: User data
        """
        return UserResponse(user_id=user_id)
    
    async def create_temp_user(self, request: TempUserRequest) -> Dict:
        """
        Create a temporary user with just a username
        
        Args:
            request: Username request
            
        Returns:
            Dict: User data with ID
        """
        if not self.user_service:
            raise HTTPException(status_code=500, detail="User service not initialized")
            
        try:
            user = await self.user_service.create_temporary_user(request.username)
            return {
                "id": user.id,
                "username": user.username,
                "is_temporary": user.is_temporary
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def link_identity(self, request: LinkIdentityRequest, user_id: str = Depends(get_current_user)) -> Dict:
        """
        Link a temporary user to an authenticated identity
        
        Args:
            request: Link request
            user_id: Authenticated user ID from token
            
        Returns:
            Dict: Updated user data
        """
        if not self.user_service:
            raise HTTPException(status_code=500, detail="User service not initialized")
            
        try:
            # Use the auth_id from the token
            user = await self.user_service.link_user_identity(
                temp_user_id=request.temp_user_id,
                auth_id=user_id,
                auth_provider=request.auth_provider,
                email=request.email,
                avatar_url=request.avatar_url
            )
            
            return {
                "id": user.id,
                "username": user.username,
                "is_temporary": user.is_temporary,
                "auth_provider": user.auth_provider.value,
                "email": user.email
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))