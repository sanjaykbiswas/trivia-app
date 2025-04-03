"""
Service for user management operations.

This module provides business logic for user creation, authentication,
and profile management.
"""
import logging
import traceback
from typing import Optional, Tuple, Dict, Any

from ..models.user import User, UserCreate, UserUpdate
# --- ADDED IMPORTS ---
from ..models.game_session import GameStatus
from ..repositories.user_repository import UserRepository
from ..repositories.game_participant_repository import GameParticipantRepository
from ..repositories.game_session_repository import GameSessionRepository
from ..models.game_participant import GameParticipantUpdate
# --- END ADDED IMPORTS ---
from ..utils import ensure_uuid

# Configure logger
logger = logging.getLogger(__name__)

class UserService:
    """
    Service for user management operations.

    Handles business logic related to creating, retrieving, updating,
    and authenticating users.
    """

    # --- MODIFIED __init__ ---
    def __init__(
        self,
        user_repository: UserRepository,
        game_participant_repository: GameParticipantRepository, # <<< ADDED
        game_session_repository: GameSessionRepository # <<< ADDED
    ):
        """
        Initialize the service with required repositories.

        Args:
            user_repository: Repository for user operations
            game_participant_repository: Repository for game participant operations
            game_session_repository: Repository for game session operations
        """
        self.user_repository = user_repository
        self.game_participant_repository = game_participant_repository # <<< ADDED
        self.game_session_repository = game_session_repository # <<< ADDED
    # --- END MODIFIED __init__ ---

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
        (No changes to this method's logic)
        """
        try:
            if email:
                existing_user = await self.user_repository.get_by_email(email)
                if existing_user:
                    logger.warning(f"User with email {email} already exists")
                    raise ValueError(f"User with email {email} already exists")

            user_data = UserCreate(
                displayname=displayname,
                email=email,
                is_temporary=is_temporary,
                auth_provider=auth_provider,
                auth_id=auth_id
            )

            user = await self.user_repository.create(obj_in=user_data)
            logger.info(f"Created new user with ID: {user.id}")

            return user

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    async def get_user(self, user_id: str) -> Optional[User]:
        """
        Get a user by ID.
        (No changes to this method)
        """
        try:
            user_id = ensure_uuid(user_id)
            return await self.user_repository.get_by_id(user_id)
        except Exception as e:
            logger.error(f"Error retrieving user {user_id}: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    # --- MODIFIED update_user ---
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
        Update a user and their display name in active/pending games.

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
        updated_user: Optional[User] = None
        try:
            user_id = ensure_uuid(user_id)
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                logger.warning(f"User with ID {user_id} not found for update")
                return None

            if email and email != user.email:
                existing_user = await self.user_repository.get_by_email(email)
                if existing_user and existing_user.id != user_id:
                    logger.warning(f"Email {email} already in use by another user")
                    raise ValueError(f"Email {email} already in use by another user")

            # --- Only create update payload if there are actual changes ---
            update_data_dict = {}
            if displayname is not None and displayname != user.displayname:
                update_data_dict['displayname'] = displayname
            if email is not None and email != user.email:
                update_data_dict['email'] = email
            if is_temporary is not None and is_temporary != user.is_temporary:
                update_data_dict['is_temporary'] = is_temporary
            if auth_provider is not None and auth_provider != user.auth_provider:
                update_data_dict['auth_provider'] = auth_provider
            if auth_id is not None and auth_id != user.auth_id:
                update_data_dict['auth_id'] = auth_id

            new_display_name_to_propagate = update_data_dict.get('displayname') # Get the name being updated

            if not update_data_dict:
                logger.info(f"No fields to update for user {user_id}")
                # --- Propagate name change even if only displayname changed ---
                if displayname is not None and displayname != user.displayname:
                    new_display_name_to_propagate = displayname
                else:
                    return user # No user record update needed, and name didn't change
            else:
                # Update the user record
                update_data = UserUpdate(**update_data_dict)
                updated_user = await self.user_repository.update(id=user_id, obj_in=update_data)
                if updated_user:
                    logger.info(f"Updated user record for ID: {user_id}")
                else:
                    logger.error(f"Failed to update user record for ID: {user_id}")
                    # Don't proceed if the primary user update failed
                    return None

            # --- Propagate display name change to active/pending game participants ---
            if new_display_name_to_propagate is not None:
                logger.info(f"Propagating name change '{new_display_name_to_propagate}' for user {user_id} to relevant games.")
                try:
                    participant_records = await self.game_participant_repository.get_user_active_games(user_id)
                    updated_count = 0
                    for participant in participant_records:
                        # Fetch game session to check status
                        game_session = await self.game_session_repository.get_by_id(participant.game_session_id)
                        if game_session and game_session.status in [GameStatus.PENDING, GameStatus.ACTIVE]:
                            # Only update if the name is actually different
                            if participant.display_name != new_display_name_to_propagate:
                                participant_update_payload = GameParticipantUpdate(display_name=new_display_name_to_propagate) # type: ignore[call-arg] # Explicitly ignore if Pydantic complains about optional/required mismatch during partial update intention
                                await self.game_participant_repository.update(id=participant.id, obj_in=participant_update_payload)
                                updated_count += 1
                        else:
                            logger.debug(f"Skipping participant {participant.id} in game {participant.game_session_id} (status: {game_session.status if game_session else 'Not Found'})")
                    logger.info(f"Updated display name for {updated_count} participant records for user {user_id}.")
                except Exception as propagation_error:
                     # Log the error but don't fail the whole user update
                     logger.error(f"Error propagating name change for user {user_id}: {propagation_error}", exc_info=True)

            # Return the updated user record (or original if only name propagation happened)
            return updated_user if updated_user else user

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    # --- END MODIFIED update_user ---


    async def delete_user(self, user_id: str) -> Optional[User]:
        """
        Delete a user.
        (No changes to this method)
        """
        try:
            user_id = ensure_uuid(user_id)
            deleted_user = await self.user_repository.delete(id=user_id)
            if deleted_user: logger.info(f"Deleted user with ID: {user_id}")
            else: logger.warning(f"User with ID {user_id} not found for deletion")
            return deleted_user
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email address.
        (No changes to this method)
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
        (No changes to this method)
        """
        try:
            user = await self.user_repository.get_by_auth_details(auth_provider, auth_id)
            if user: return user, False
            new_user = await self.create_user(
                displayname=displayname, email=email, is_temporary=is_temporary,
                auth_provider=auth_provider, auth_id=auth_id
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
        (No changes to this method logic, but it now calls the modified update_user)
        """
        try:
            user_id = ensure_uuid(user_id)
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                logger.warning(f"User with ID {user_id} not found for conversion")
                return None
            if not user.is_temporary:
                logger.warning(f"User with ID {user_id} is not a temporary user")
                raise ValueError(f"User with ID {user_id} is not a temporary user")
            if email:
                existing_user = await self.user_repository.get_by_email(email)
                if existing_user and existing_user.id != user_id:
                    logger.warning(f"Email {email} already in use by another user")
                    raise ValueError(f"Email {email} already in use by another user")

            # This call now uses the modified update_user method
            updated_user = await self.update_user(
                user_id=user_id, displayname=displayname, email=email,
                is_temporary=False, auth_provider=auth_provider, auth_id=auth_id
            )

            if updated_user: logger.info(f"Converted temporary user {user_id} to permanent account")
            return updated_user
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error converting temporary user {user_id}: {str(e)}")
            logger.error(traceback.format_exc())
            raise