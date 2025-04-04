# backend/src/services/user_service.py
"""
Service for user management operations.

This module provides business logic for user creation, authentication,
and profile management, including broadcasting updates via WebSockets.
"""
import logging
import traceback
import asyncio
from typing import Optional, Tuple, Dict, Any, List

from ..models.user import User, UserCreate, UserUpdate
from ..models.game_session import GameStatus
from ..repositories.user_repository import UserRepository
from ..repositories.game_participant_repository import GameParticipantRepository
from ..repositories.game_session_repository import GameSessionRepository
from ..models.game_participant import GameParticipantUpdate

# --- WebSocket Integration ---
from ..websocket_manager import ConnectionManager
# --- End WebSocket Integration ---

from ..utils import ensure_uuid

# Configure logger
logger = logging.getLogger(__name__)

class UserService:
    """
    Service for user management operations.

    Handles business logic related to creating, retrieving, updating,
    and authenticating users. Propagates display name changes to games
    via database updates and WebSocket broadcasts.
    """

    # --- MODIFIED __init__ ---
    def __init__(
        self,
        user_repository: UserRepository,
        game_participant_repository: GameParticipantRepository,
        game_session_repository: GameSessionRepository,
        connection_manager: ConnectionManager # <<< ADDED
    ):
        """
        Initialize the service with required repositories and connection manager.
        """
        self.user_repository = user_repository
        self.game_participant_repository = game_participant_repository
        self.game_session_repository = game_session_repository
        self.connection_manager = connection_manager # <<< ADDED
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
        Create a new user. (No changes needed here for WS)
        """
        try:
            if email:
                existing_user = await self.user_repository.get_by_email(email)
                if existing_user:
                    logger.warning(f"User with email {email} already exists")
                    raise ValueError(f"User with email {email} already exists")

            user_data = UserCreate(
                displayname=displayname, email=email, is_temporary=is_temporary,
                auth_provider=auth_provider, auth_id=auth_id
            )
            user = await self.user_repository.create(obj_in=user_data)
            logger.info(f"Created new user with ID: {user.id}")
            return user

        except ValueError: raise
        except Exception as e: logger.error(f"Error creating user: {str(e)}"); logger.error(traceback.format_exc()); raise

    async def get_user(self, user_id: str) -> Optional[User]:
        """ Get a user by ID. (No changes needed here) """
        try:
            user_id_str = ensure_uuid(user_id)
            return await self.user_repository.get_by_id(user_id_str)
        except Exception as e: logger.error(f"Error retrieving user {user_id}: {str(e)}"); logger.error(traceback.format_exc()); raise

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
        Update a user and propagate display name changes via DB and WebSockets.
        """
        updated_user_record: Optional[User] = None
        name_changed = False
        new_display_name: Optional[str] = None

        try:
            user_id_str = ensure_uuid(user_id)
            user = await self.user_repository.get_by_id(user_id_str)
            if not user: logger.warning(f"User with ID {user_id_str} not found for update"); return None

            if email and email != user.email:
                existing_email_user = await self.user_repository.get_by_email(email)
                if existing_email_user and existing_email_user.id != user_id_str:
                    raise ValueError(f"Email {email} already in use by another user")

            update_data_dict = {}
            if displayname is not None and displayname != user.displayname:
                update_data_dict['displayname'] = displayname
                name_changed = True
                new_display_name = displayname
            if email is not None and email != user.email: update_data_dict['email'] = email
            if is_temporary is not None and is_temporary != user.is_temporary: update_data_dict['is_temporary'] = is_temporary
            if auth_provider is not None and auth_provider != user.auth_provider: update_data_dict['auth_provider'] = auth_provider
            if auth_id is not None and auth_id != user.auth_id: update_data_dict['auth_id'] = auth_id

            if not update_data_dict:
                logger.info(f"No fields to update for user {user_id_str}")
                updated_user_record = user # Return the original if no DB update needed
            else:
                update_data = UserUpdate(**update_data_dict)
                updated_user_record = await self.user_repository.update(id=user_id_str, obj_in=update_data)
                if updated_user_record: logger.info(f"Updated user record for ID: {user_id_str}")
                else: logger.error(f"Failed to update user record for ID: {user_id_str}"); return None

            # --- Propagate display name change ---
            if name_changed and new_display_name is not None:
                logger.info(f"Propagating name change '{new_display_name}' for user {user_id_str}")
                await self._propagate_name_change(user_id_str, new_display_name)

            return updated_user_record

        except ValueError: raise
        except Exception as e: logger.error(f"Error updating user {user_id_str}: {str(e)}"); logger.error(traceback.format_exc()); raise
    # --- END MODIFIED update_user ---

    # --- NEW Helper Method: _propagate_name_change ---
    async def _propagate_name_change(self, user_id: str, new_display_name: str):
        """Propagates name change to active/pending games via DB and WebSocket."""
        try:
            participant_records = await self.game_participant_repository.get_user_active_games(user_id)
            game_ids_to_notify: List[str] = []
            update_tasks = []

            for participant in participant_records:
                # Check game status before updating participant record
                game_session = await self.game_session_repository.get_by_id(participant.game_session_id)
                if game_session and game_session.status in [GameStatus.PENDING, GameStatus.ACTIVE]:
                    if participant.display_name != new_display_name:
                        # Schedule DB update
                        participant_update_payload = GameParticipantUpdate(display_name=new_display_name) # type: ignore[call-arg]
                        update_tasks.append(
                           asyncio.create_task(self.game_participant_repository.update(id=participant.id, obj_in=participant_update_payload))
                        )
                        if participant.game_session_id not in game_ids_to_notify:
                           game_ids_to_notify.append(participant.game_session_id)
                    # Include game ID even if DB name was already correct, in case WS connection state is different
                    elif participant.game_session_id not in game_ids_to_notify:
                         game_ids_to_notify.append(participant.game_session_id)

            # Execute DB updates concurrently
            db_update_results = await asyncio.gather(*update_tasks, return_exceptions=True)
            failed_db_updates = [res for res in db_update_results if isinstance(res, Exception) or res is None]
            if failed_db_updates: logger.warning(f"Failed {len(failed_db_updates)} participant DB name updates for user {user_id}.")

            # Broadcast WebSocket update to relevant game rooms
            if game_ids_to_notify:
                message = {
                    "type": "user_name_updated",
                    "payload": {"user_id": user_id, "new_display_name": new_display_name}
                }
                broadcast_tasks = [self.connection_manager.broadcast(message, game_id) for game_id in game_ids_to_notify]
                await asyncio.gather(*broadcast_tasks, return_exceptions=True) # Log errors within broadcast
                logger.info(f"Broadcasted name update for user {user_id} to {len(game_ids_to_notify)} games.")

        except Exception as propagation_error:
            logger.error(f"Error propagating name change for user {user_id}: {propagation_error}", exc_info=True)
    # --- END NEW Helper Method ---

    async def delete_user(self, user_id: str) -> Optional[User]:
        """ Delete a user. (No changes needed here) """
        try:
            user_id_str = ensure_uuid(user_id)
            deleted_user = await self.user_repository.delete(id=user_id_str)
            if deleted_user: logger.info(f"Deleted user with ID: {user_id_str}")
            else: logger.warning(f"User with ID {user_id_str} not found for deletion")
            return deleted_user
        except Exception as e: logger.error(f"Error deleting user {user_id_str}: {str(e)}"); logger.error(traceback.format_exc()); raise

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """ Get a user by email address. (No changes needed here) """
        try: return await self.user_repository.get_by_email(email)
        except Exception as e: logger.error(f"Error retrieving user by email {email}: {str(e)}"); logger.error(traceback.format_exc()); raise

    async def get_or_create_user_by_auth(
        self, auth_provider: str, auth_id: str, email: Optional[str] = None,
        displayname: Optional[str] = None, is_temporary: bool = False
    ) -> Tuple[User, bool]:
        """ Get/Create user by auth details. (No changes needed here) """
        try:
            user = await self.user_repository.get_by_auth_details(auth_provider, auth_id)
            if user: return user, False
            new_user = await self.create_user(displayname=displayname, email=email, is_temporary=is_temporary, auth_provider=auth_provider, auth_id=auth_id)
            return new_user, True
        except Exception as e: logger.error(f"Error in get_or_create_user_by_auth: {str(e)}"); logger.error(traceback.format_exc()); raise

    async def convert_temporary_user(
        self, user_id: str, displayname: str, email: Optional[str] = None,
        auth_provider: Optional[str] = None, auth_id: Optional[str] = None
    ) -> Optional[User]:
        """ Convert temporary user. (No changes needed here, calls updated `update_user`) """
        try:
            user_id_str = ensure_uuid(user_id)
            user = await self.user_repository.get_by_id(user_id_str)
            if not user: logger.warning(f"User with ID {user_id_str} not found for conversion"); return None
            if not user.is_temporary: raise ValueError(f"User with ID {user_id_str} is not a temporary user")
            # Update call will now handle propagation
            updated_user = await self.update_user( user_id=user_id_str, displayname=displayname, email=email, is_temporary=False, auth_provider=auth_provider, auth_id=auth_id )
            if updated_user: logger.info(f"Converted temporary user {user_id_str} to permanent account")
            return updated_user
        except ValueError: raise
        except Exception as e: logger.error(f"Error converting temporary user {user_id_str}: {str(e)}"); logger.error(traceback.format_exc()); raise