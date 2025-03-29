# backend/src/services/user_service.py
from typing import Dict, Any, Optional
import uuid
from models.user import User, AuthProvider
from utils.supabase_actions import SupabaseActions
import logging

# Configure logger
logger = logging.getLogger(__name__)

class UserService:
    """
    Service for managing users
    
    This service handles user creation, authentication, and profile management
    """
    def __init__(self, supabase_client):
        """
        Initialize user service with Supabase client
        
        Args:
            supabase_client: Initialized Supabase client
        """
        self.supabase_actions = SupabaseActions(supabase_client)
    
    async def create_temporary_user(self, username: str) -> User:
        """
        Create a temporary user with just a username
        
        Args:
            username (str): User's display name
            
        Returns:
            User: Created user
        """
        try:
            logger.info(f"Creating temporary user with username: {username}")
            
            # Use the SupabaseActions to create the temporary user
            user_data = await self.supabase_actions.create_temporary_user(username)
            
            # Convert to User object
            user = User.from_dict(user_data)
            
            logger.info(f"Temporary user created with ID: {user.id}")
            return user
        except Exception as e:
            logger.error(f"Error creating temporary user: {e}")
            raise
    
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
        try:
            logger.info(f"Linking user {temp_user_id} to auth identity {auth_id}")
            
            # Validate auth provider
            try:
                provider = AuthProvider(auth_provider)
            except ValueError:
                provider = AuthProvider.NONE
                logger.warning(f"Invalid auth provider: {auth_provider}, using NONE")
            
            # Use the SupabaseActions to link the user identity
            user_data = await self.supabase_actions.link_user_identity(
                temp_user_id=temp_user_id,
                auth_id=auth_id,
                auth_provider=provider.value,
                email=email,
                avatar_url=avatar_url
            )
            
            # Convert to User object
            user = User.from_dict(user_data)
            
            logger.info(f"User {temp_user_id} linked to auth identity {auth_id}")
            return user
        except Exception as e:
            logger.error(f"Error linking user identity: {e}")
            raise
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get a user by ID
        
        Args:
            user_id (str): User ID
            
        Returns:
            Optional[User]: User if found
        """
        try:
            # Use the SupabaseActions to ensure the user exists
            user_data = await self.supabase_actions.ensure_user_exists(user_id)
            
            if user_data:
                return User.from_dict(user_data)
            return None
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
    
    async def find_user_by_auth(self, auth_id: str, auth_provider: str) -> Optional[User]:
        """
        Find a user by authentication credentials
        
        Args:
            auth_id (str): Authentication provider's user ID
            auth_provider (str): Authentication provider name
            
        Returns:
            Optional[User]: User if found
        """
        try:
            # Use the SupabaseActions to find the user
            user_data = await self.supabase_actions.find_user_by_auth(auth_id, auth_provider)
            
            if user_data:
                return User.from_dict(user_data)
            return None
        except Exception as e:
            logger.error(f"Error finding user by auth: {e}")
            return None