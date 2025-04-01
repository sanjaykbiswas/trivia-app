# backend/src/repositories/game_participant_repository.py
import uuid
from typing import List, Optional
from supabase import AsyncClient

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
        # Ensure game_session_id is a valid UUID string
        game_session_id_str = ensure_uuid(game_session_id)
        
        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("game_session_id", game_session_id_str)
        )
        response = await self._execute_query(query)
        return [self.model.parse_obj(item) for item in response.data]

    async def get_by_user_and_game(self, user_id: str, game_session_id: str) -> Optional[GameParticipant]:
        """Retrieve a participant by user ID and game session ID."""
        # Ensure UUIDs are valid UUID strings
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
            return self.model.parse_obj(response.data[0])
        return None

    async def update_score(self, participant_id: str, new_score: int) -> Optional[GameParticipant]:
        """Update a participant's score."""
        # Ensure participant_id is a valid UUID string
        participant_id_str = ensure_uuid(participant_id)
        
        update_data = {
            "score": new_score,
            "last_activity": self._serialize_data_for_db({"last_activity": GameParticipantUpdate().last_activity})["last_activity"]
        }
        
        query = self.db.table(self.table_name).update(update_data).eq("id", participant_id_str)
        await self._execute_query(query)
        
        # Fetch and return the updated object
        return await self.get_by_id(participant_id)

    async def get_user_active_games(self, user_id: str) -> List[GameParticipant]:
        """Retrieve all active games a user is participating in."""
        # Ensure user_id is a valid UUID string
        user_id_str = ensure_uuid(user_id)
        
        # This query will need to be joined with game_sessions in a real implementation
        # For now, we'll just get all games the user is in and filter later in the service
        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("user_id", user_id_str)
        )
        response = await self._execute_query(query)
        return [self.model.parse_obj(item) for item in response.data]