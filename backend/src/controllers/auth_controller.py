from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from utils.auth import get_current_user
from typing import Dict

class UserResponse(BaseModel):
    user_id: str

class AuthController:
    """
    Controller for authentication-related endpoints
    """
    def __init__(self):
        self.router = APIRouter(prefix="/auth", tags=["auth"])
        self._setup_routes()
    
    def _setup_routes(self):
        """Set up API routes"""
        self.router.get("/me", response_model=UserResponse)(self.get_current_user)
    
    async def get_current_user(self, user_id: str = Depends(get_current_user)) -> UserResponse:
        """
        Get current authenticated user
        
        Args:
            user_id: User ID from token
        
        Returns:
            UserResponse: User data
        """
        return UserResponse(user_id=user_id)