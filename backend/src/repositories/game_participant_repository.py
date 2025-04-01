# backend/src/repositories/game_participant_repository.py
import uuid
from typing import List, Optional
from supabase import AsyncClient
from datetime import datetime, timezone # Import datetime, timezone

from ..models.game_participant import GameParticipant, GameParticipantCreate, GameParticipantUpdate
from .base_repository_impl import BaseRepositoryImpl
from ..utils import ensure_uuid

class GameParticipantRepository(BaseRepositoryImpl[GameParticipant, GameParticipantCreate, GameParticipantUpdate, str]):
    """
    Repository for managing GameParticipant data in Supabase.
    """
    def __init__(self, db: AsyncClient):
        super().__init__(model=GameParticipant, db=db, table_name="game_participants") # Table name: "game_participants"

    # --- Custom GameParticipant-specific methods ---

    async def get_by_game_session_id(self, game_session_id: str) -> List[GameParticipant]:
        """Retrieve all participants for a specific game session."""
        game_session_id_str = ensure_uuid(game_session_id)
        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("game_session_id", game_session_id_str)
        )
        response = await self._execute_query(query)
        # Use model_validate for Pydantic V2
        return [self.model.model_validate(item) for item in response.data]

    async def get_by_user_and_game(self, user_id: str, game_session_id: str) -> Optional[GameParticipant]:
        """Retrieve a participant by user ID and game session ID."""
        user_id_str = ensure_uuid(user_id)
        game_session_id_str = ensure_uuid(game_session_id)
        query = (
            self.db.table(self.table_name)
            .select("*")
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

        # --- FIX: Explicitly convert datetime to ISO string ---
        # Get the current time in UTC and format it as ISO 8601 string
        now_iso = datetime.now(timezone.utc).isoformat() + "Z" # Append 'Z' for UTC indicator
        update_data = {
            "score": new_score,
            "last_activity": now_iso # Use the ISO string directly
        }
        # --- END FIX ---

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
            .select("*")
            .eq("user_id", user_id_str)
        )
        response = await self._execute_query(query)
        # Use model_validate for Pydantic V2
        return [self.model.model_validate(item) for item in response.data]