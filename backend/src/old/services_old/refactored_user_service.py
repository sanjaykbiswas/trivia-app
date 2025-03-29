# backend/src/services/refactored_user_service.py
from typing import Dict, Any, Optional
import logging
from models.user import User, AuthProvider
from services.service_base import ServiceBase
from repositories.user_repository import UserRepository
from utils.error_handling import async_handle_errors

# Configure logger
logger = logging.getLogger(__name__)

class RefactoredUserService(ServiceBase):
    """
    Refactored service for managing users
    
    This service handles user creation, authentication, and profile management
    """
    def __init__(self, user_repository: UserRepository):
        """
        Initialize user service with repository
        
        Args:
            user_repository (UserRepository): Repository for user operations
        """
        # Initialize with the user repository
        super().__init__(user_repository)
    
    @async_handle_errors
    async def create_temporary_user(self, username: str) -> User:
        """
        Create a temporary user with just a username
        
        Args:
            username (str): User's display name
            
        Returns:
            User: Created user
        """
        logger.info(f"Creating temporary user with username: {username}")
        
        # Cast repository to UserRepository to access specific methods
        user_repo = self.repository
        
        # Create temporary user using repository
        user = await user_repo.create_temporary_user(username)
        
        logger.info(f"Temporary user created with ID: {user.id}")
        return user
    
    @async_handle_errors
    async def link_user_identity(
        self, 
        temp_user_id: str,
        auth_id: str,
        auth_provider: str,
        email: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> User:
        """
        Link a temporary user to an authenticated identity
        
        Args:
            temp_user_id (str): Temporary user ID
            auth_id (str): Authentication provider's user ID
            auth_provider (str): Authentication provider name
            email (Optional[str]): User's email
            avatar_url (Optional[str]): User's avatar URL
            
        Returns:
            User: Updated user
        """
        logger.info(f"Linking user {temp_user_id} to auth identity {auth_id}")
        
        # Validate auth provider
        try:
            provider = AuthProvider(auth_provider)
        except ValueError:
            provider = AuthProvider.NONE
            logger.warning(f"Invalid auth provider: {auth_provider}, using NONE")
        
        # Cast repository to UserRepository to access specific methods
        user_repo = self.repository
        
        # Link user identity using repository
        user = await user_repo.link_user_identity(
            temp_user_id=temp_user_id,
            auth_id=auth_id,
            auth_provider=provider.value,
            email=email,
            avatar_url=avatar_url
        )
        
        logger.info(f"User {temp_user_id} linked to auth identity {auth_id}")
        return user
    
    @async_handle_errors
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get a user by ID
        
        Args:
            user_id (str): User ID
            
        Returns:
            Optional[User]: User if found
        """
        # Cast repository to UserRepository to access specific methods
        user_repo = self.repository
        
        # Ensure user exists using repository
        return await user_repo.ensure_user_exists(user_id)
    
    @async_handle_errors
    async def find_user_by_auth(self, auth_id: str, auth_provider: str) -> Optional[User]:
        """
        Find a user by authentication credentials
        
        Args:
            auth_id (str): Authentication provider's user ID
            auth_provider (str): Authentication provider name
            
        Returns:
            Optional[User]: User if found
        """
        # Cast repository to UserRepository to access specific methods
        user_repo = self.repository
        
        # Find user by auth using repository
        return await user_repo.get_by_auth(auth_id, auth_provider)