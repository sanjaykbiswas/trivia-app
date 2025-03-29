# backend/src/repositories/user_repository.py
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
from models.user import User, AuthProvider
from repositories.base_repository_impl import BaseRepositoryImpl

# Configure logger
logger = logging.getLogger(__name__)

class UserRepository(BaseRepositoryImpl[User]):
    """
    Repository for managing users in the database
    """
    def __init__(self, supabase_client):
        """
        Initialize with Supabase client
        
        Args:
            supabase_client: Initialized Supabase client
        """
        super().__init__(supabase_client, "users", User)
    
    async def get_by_auth(self, auth_id: str, auth_provider: str) -> Optional[User]:
        """
        Find a user by authentication credentials
        
        Args:
            auth_id (str): Authentication provider's user ID
            auth_provider (str): Authentication provider name
            
        Returns:
            Optional[User]: User if found
        """
        response = (
            self.client
            .table(self.table_name)
            .select("*")
            .eq("auth_id", auth_id)
            .eq("auth_provider", auth_provider)
            .execute()
        )
        
        if response.data and len(response.data) > 0:
            return User.from_dict(response.data[0])
        
        return None
    
    async def create_temporary_user(self, username: str) -> User:
        """
        Create a temporary user with just a username
        
        Args:
            username (str): User's display name
            
        Returns:
            User: Created user with generated ID
        """
        logger.info(f"Creating temporary user with username: {username}")
        
        # Create user data
        user = User(
            username=username,
            is_temporary=True,
            auth_provider=AuthProvider.NONE,
            created_at=datetime.now()
        )
        
        # Insert into users table
        created_user = await self.create(user)
        
        if created_user and created_user.id:
            logger.info(f"Temporary user created with ID: {created_user.id}")
            return created_user
        else:
            logger.error(f"Failed to create temporary user")
            raise ValueError(f"Failed to create temporary user")
    
    async def ensure_user_exists(self, user_id: str, username: Optional[str] = None) -> User:
        """
        Ensure a user exists in the database, creating if necessary
        
        Args:
            user_id (str): User ID
            username (str, optional): Username for new user
            
        Returns:
            User: User object
        """
        logger.info(f"Ensuring user exists: {user_id}")
        
        # Check if user exists
        user = await self.get_by_id(user_id)
        
        # If user exists, return user
        if user:
            logger.info(f"User {user_id} already exists")
            return user
        
        # User doesn't exist, create new user (primarily for temporary users)
        logger.info(f"Creating new user: {user_id}")
        
        new_user = User(
            id=user_id,
            username=username or f"User_{user_id[:8]}", # Default username if none provided
            is_temporary=True,
            auth_provider=AuthProvider.NONE
        )
        
        created_user = await self.create(new_user)
        
        if created_user and created_user.id:
            logger.info(f"User {user_id} created successfully")
            return created_user
        else:
            logger.error(f"Failed to create user with ID: {user_id}")
            raise ValueError(f"Failed to create user with ID: {user_id}")
    
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
            email (str, optional): User's email
            avatar_url (str, optional): User's avatar URL
            
        Returns:
            User: Updated user
        """
        logger.info(f"Linking user {temp_user_id} to auth identity {auth_id} from {auth_provider}")
        
        # First, check if the user exists
        user = await self.get_by_id(temp_user_id)
        
        if not user:
            logger.error(f"User {temp_user_id} not found")
            raise ValueError(f"User {temp_user_id} not found")
        
        # Check if this is a temporary user
        if not user.is_temporary:
            logger.warning(f"User {temp_user_id} is already linked to an auth provider")
            return user  # Return existing data
        
        # Update user with auth information
        update_data = {
            "is_temporary": False,
            "auth_provider": auth_provider,
            "auth_id": auth_id
        }
        
        # Add optional fields if provided
        if email:
            update_data["email"] = email
        
        if avatar_url:
            update_data["avatar_url"] = avatar_url
        
        # Update the user record
        updated_user = await self.update(temp_user_id, update_data)
        
        if updated_user:
            logger.info(f"User {temp_user_id} successfully linked to auth identity")
            return updated_user
        else:
            logger.error(f"Failed to update user {temp_user_id}")
            raise ValueError(f"Failed to update user {temp_user_id}")