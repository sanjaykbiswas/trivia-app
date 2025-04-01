"""
Service for user management operations.

This module provides business logic for user creation, authentication,
and profile management.
"""
import logging
import traceback
from typing import Optional, Tuple, Dict, Any

from ..models.user import User, UserCreate, UserUpdate
from ..repositories.user_repository import UserRepository
from ..utils import ensure_uuid

# Configure logger
logger = logging.getLogger(__name__)

class UserService:
    """
    Service for user management operations.
    
    Handles business logic related to creating, retrieving, updating,
    and authenticating users.
    """
    
    def __init__(self, user_repository: UserRepository):
        """
        Initialize the service with required repositories.
        
        Args:
            user_repository: Repository for user operations
        """
        self.user_repository = user_repository
    
    async def create_user(
        self,
        displayname: Optional[str] = None,
        email: Optional[str] = None,
        is_temporary: bool = False,
        auth_provider: Optional[str] = None,
        auth_id: Optional[str] = None
    ) -> User:
        """
        Create a new user.
        
        Args:
            displayname: Optional display name for the user
            email: Optional email address
            is_temporary: Whether this is a temporary user account
            auth_provider: Optional authentication provider (e.g., 'google', 'facebook')
            auth_id: Optional identifier from the authentication provider
            
        Returns:
            Created User object
        """
        try:
            # Check if user with this email already exists
            if email:
                existing_user = await self.user_repository.get_by_email(email)
                if existing_user:
                    logger.warning(f"User with email {email} already exists")
                    raise ValueError(f"User with email {email} already exists")
            
            # Create user data
            user_data = UserCreate(
                displayname=displayname,
                email=email,
                is_temporary=is_temporary,
                auth_provider=auth_provider,
                auth_id=auth_id
            )
            
            # Create the user
            user = await self.user_repository.create(obj_in=user_data)
            logger.info(f"Created new user with ID: {user.id}")
            
            return user
            
        except ValueError:
            # Re-raise value errors for proper handling
            raise
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """
        Get a user by ID.
        
        Args:
            user_id: ID of the user to retrieve
            
        Returns:
            User object or None if not found
        """
        try:
            # Ensure user_id is a valid UUID string
            user_id = ensure_uuid(user_id)
            
            return await self.user_repository.get_by_id(user_id)
            
        except Exception as e:
            logger.error(f"Error retrieving user {user_id}: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    async def update_user(
        self,
        user_id: str,
        displayname: Optional[str] = None,
        email: Optional[str] = None,
        is_temporary: Optional[bool] = None,
        auth_provider: Optional[str] = None,
        auth_id: Optional[str] = None
    ) -> Optional[User]:
        """
        Update a user.
        
        Args:
            user_id: ID of the user to update
            displayname: New display name (if provided)
            email: New email address (if provided)
            is_temporary: New temporary status (if provided)
            auth_provider: New authentication provider (if provided)
            auth_id: New authentication ID (if provided)
            
        Returns:
            Updated User object or None if user not found
        """
        try:
            # Ensure user_id is a valid UUID string
            user_id = ensure_uuid(user_id)
            
            # Check if user exists
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                logger.warning(f"User with ID {user_id} not found for update")
                return None
            
            # Check if new email already exists for a different user
            if email and email != user.email:
                existing_user = await self.user_repository.get_by_email(email)
                if existing_user and existing_user.id != user_id:
                    logger.warning(f"Email {email} already in use by another user")
                    raise ValueError(f"Email {email} already in use by another user")
            
            # Prepare update data
            update_data = UserUpdate(
                displayname=displayname,
                email=email,
                is_temporary=is_temporary,
                auth_provider=auth_provider,
                auth_id=auth_id
            )
            
            # Update the user
            updated_user = await self.user_repository.update(id=user_id, obj_in=update_data)
            logger.info(f"Updated user with ID: {user_id}")
            
            return updated_user
            
        except ValueError:
            # Re-raise value errors for proper handling
            raise
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    async def delete_user(self, user_id: str) -> Optional[User]:
        """
        Delete a user.
        
        Args:
            user_id: ID of the user to delete
            
        Returns:
            Deleted User object or None if user not found
        """
        try:
            # Ensure user_id is a valid UUID string
            user_id = ensure_uuid(user_id)
            
            # Delete the user
            deleted_user = await self.user_repository.delete(id=user_id)
            
            if deleted_user:
                logger.info(f"Deleted user with ID: {user_id}")
            else:
                logger.warning(f"User with ID {user_id} not found for deletion")
            
            return deleted_user
            
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email address.
        
        Args:
            email: Email address to search for
            
        Returns:
            User object or None if not found
        """
        try:
            return await self.user_repository.get_by_email(email)
            
        except Exception as e:
            logger.error(f"Error retrieving user by email {email}: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    async def get_or_create_user_by_auth(
        self,
        auth_provider: str,
        auth_id: str,
        email: Optional[str] = None,
        displayname: Optional[str] = None,
        is_temporary: bool = False
    ) -> Tuple[User, bool]:
        """
        Get a user by authentication details or create a new one if not found.
        
        Args:
            auth_provider: Authentication provider (e.g., 'google', 'facebook')
            auth_id: Identifier from the authentication provider
            email: Optional email address for new user
            displayname: Optional display name for new user
            is_temporary: Whether to create a temporary user if not found
            
        Returns:
            Tuple containing:
                - User object
                - Boolean indicating if user was newly created
        """
        try:
            # Try to find user by auth details
            user = await self.user_repository.get_by_auth_details(auth_provider, auth_id)
            
            if user:
                # User found
                return user, False
            
            # User not found, create a new one
            new_user = await self.create_user(
                displayname=displayname,
                email=email,
                is_temporary=is_temporary,
                auth_provider=auth_provider,
                auth_id=auth_id
            )
            
            return new_user, True
            
        except Exception as e:
            logger.error(f"Error in get_or_create_user_by_auth: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    async def convert_temporary_user(
        self,
        user_id: str,
        displayname: str,
        email: Optional[str] = None,
        auth_provider: Optional[str] = None,
        auth_id: Optional[str] = None
    ) -> Optional[User]:
        """
        Convert a temporary user to a permanent one.
        
        Args:
            user_id: ID of the temporary user to convert
            displayname: Display name for the user
            email: Optional email address
            auth_provider: Optional authentication provider
            auth_id: Optional authentication ID
            
        Returns:
            Updated User object or None if user not found or not temporary
            
        Raises:
            ValueError: If user is not a temporary user
        """
        try:
            # Ensure user_id is a valid UUID string
            user_id = ensure_uuid(user_id)
            
            # Get the user
            user = await self.user_repository.get_by_id(user_id)
            
            if not user:
                logger.warning(f"User with ID {user_id} not found for conversion")
                return None
            
            # Check if user is temporary
            if not user.is_temporary:
                logger.warning(f"User with ID {user_id} is not a temporary user")
                raise ValueError(f"User with ID {user_id} is not a temporary user")
            
            # Check if email already exists for a different user
            if email:
                existing_user = await self.user_repository.get_by_email(email)
                if existing_user and existing_user.id != user_id:
                    logger.warning(f"Email {email} already in use by another user")
                    raise ValueError(f"Email {email} already in use by another user")
            
            # Update the user
            updated_user = await self.update_user(
                user_id=user_id,
                displayname=displayname,
                email=email,
                is_temporary=False,
                auth_provider=auth_provider,
                auth_id=auth_id
            )
            
            if updated_user:
                logger.info(f"Converted temporary user {user_id} to permanent account")
            
            return updated_user
            
        except ValueError:
            # Re-raise value errors for proper handling
            raise
        except Exception as e:
            logger.error(f"Error converting temporary user {user_id}: {str(e)}")
            logger.error(traceback.format_exc())
            raise