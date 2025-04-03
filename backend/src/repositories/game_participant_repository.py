# backend/src/repositories/game_participant_repository.py
import uuid
import logging # Import logging
from typing import List, Optional
from supabase import AsyncClient
from datetime import datetime, timezone # Import datetime, timezone

from ..models.game_participant import GameParticipant, GameParticipantCreate, GameParticipantUpdate
from .base_repository_impl import BaseRepositoryImpl
from ..utils import ensure_uuid

# Configure logger
logger = logging.getLogger(__name__)

class GameParticipantRepository(BaseRepositoryImpl[GameParticipant, GameParticipantCreate, GameParticipantUpdate, str]):
    """
    Repository for managing GameParticipant data in Supabase.
    """
    def __init__(self, db: AsyncClient):
        super().__init__(model=GameParticipant, db=db, table_name="game_participants") # Table name: "game_participants"

    # --- Custom GameParticipant-specific methods ---

    # --- MODIFIED get_by_game_session_id ---
    async def get_by_game_session_id(self, game_session_id: str) -> List[GameParticipant]:
        """
        Retrieve all participants for a specific game session, including the
        latest display name from the users table.
        """
        game_session_id_str = ensure_uuid(game_session_id)
        try:
            # Use select() to fetch participant columns and the related user's displayname
            # Assumes a foreign key relationship 'user_id' in 'game_participants' referencing 'id' in 'users'
            # and that the relationship is set up in Supabase for this syntax to work easily.
            # If the relationship isn't explicitly defined in Supabase, a manual join/lookup might be needed.
            # This syntax fetches all columns from game_participants and the displayname from users.
            query = (
                self.db.table(self.table_name)
                .select("*, users(displayname)") # Fetch all participant fields and user's displayname
                .eq("game_session_id", game_session_id_str)
            )
            response = await self._execute_query(query)

            participants = []
            for item in response.data:
                # Extract the user's displayname if available
                user_data = item.get('users')
                latest_display_name = user_data.get('displayname') if isinstance(user_data, dict) else None

                # Create the GameParticipant object
                # We prioritize the latest_display_name from the users table
                # If it's missing (e.g., user deleted?), fall back to the stored participant name
                participant_data = item.copy()
                if 'users' in participant_data: # Remove the nested user data before validation
                    del participant_data['users']

                # Use the fetched user display name if available, otherwise keep the one stored in the participant record
                if latest_display_name is not None:
                    participant_data['display_name'] = latest_display_name
                elif 'display_name' not in participant_data: # Ensure display_name exists
                    participant_data['display_name'] = "Unknown Player" # Fallback

                try:
                     # Use model_validate for Pydantic V2
                     participant_obj = self.model.model_validate(participant_data)
                     participants.append(participant_obj)
                except Exception as validation_error:
                     logger.error(f"Validation error parsing participant data: {validation_error}. Data: {participant_data}", exc_info=True)
                     # Optionally skip this participant or create a default representation

            return participants

        except Exception as e:
            logger.error(f"Error retrieving participants for game session {game_session_id_str}: {e}", exc_info=True)
            raise # Re-raise the exception after logging

    # --- END MODIFIED get_by_game_session_id ---

    async def get_by_user_and_game(self, user_id: str, game_session_id: str) -> Optional[GameParticipant]:
        """Retrieve a participant by user ID and game session ID."""
        user_id_str = ensure_uuid(user_id)
        game_session_id_str = ensure_uuid(game_session_id)
        query = (
            self.db.table(self.table_name)
            .select("*") # No need to join here, as we usually need the participant record itself
            .eq("user_id", user_id_str)
            .eq("game_session_id", game_session_id_str)
            .limit(1)
        )
        response = await self._execute_query(query)
        if response.data:
            # Use model_validate for Pydantic V2
            return self.model.model_validate(response.data[0])
        return None

    async def update_score(self, participant_id: str, new_score: int) -> Optional[GameParticipant]:
        """Update a participant's score and last activity time."""
        participant_id_str = ensure_uuid(participant_id)

        # --- CORRECTED FIX: Use standard ISO format ---
        # Get the current time in UTC and format it as ISO 8601 string
        # The isoformat() method correctly includes the UTC offset (+00:00)
        now_iso = datetime.now(timezone.utc).isoformat() # REMOVED + "Z"
        update_data = {
            "score": new_score,
            "last_activity": now_iso # Use the ISO string directly
        }
        # --- END CORRECTED FIX ---

        query = self.db.table(self.table_name).update(update_data).eq("id", participant_id_str)
        await self._execute_query(query) # This should now work

        # Fetch and return the updated object using the correct ID
        return await self.get_by_id(participant_id_str) # Ensure correct ID type

    async def get_user_active_games(self, user_id: str) -> List[GameParticipant]:
        """Retrieve all game participations for a user."""
        # Note: This currently returns *all* participations. Filtering by active game
        # status would typically happen in the service layer by joining/checking game status.
        user_id_str = ensure_uuid(user_id)
        query = (
            self.db.table(self.table_name)
            .select("*") # Keep simple select here, join is not needed for this specific use case
            .eq("user_id", user_id_str)
        )
        response = await self._execute_query(query)
        # Use model_validate for Pydantic V2
        return [self.model.model_validate(item) for item in response.data]