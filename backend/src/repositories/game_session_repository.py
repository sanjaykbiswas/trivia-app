# backend/src/repositories/game_session_repository.py
import uuid
from typing import List, Optional
from supabase import AsyncClient
from datetime import datetime # Import datetime

from ..models.game_session import GameSession, GameSessionCreate, GameSessionUpdate, GameStatus
from .base_repository_impl import BaseRepositoryImpl
from ..utils import ensure_uuid

class GameSessionRepository(BaseRepositoryImpl[GameSession, GameSessionCreate, GameSessionUpdate, str]):
    """
    Repository for managing GameSession data in Supabase.
    """
    def __init__(self, db: AsyncClient):
        super().__init__(model=GameSession, db=db, table_name="game_sessions") # Table name: "game_sessions"

    # --- Custom GameSession-specific methods ---

    async def get_by_code(self, code: str) -> Optional[GameSession]:
        """Retrieve a game session by its join code."""
        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("code", code)
            .limit(1)
        )
        response = await self._execute_query(query)
        if response.data:
            return self.model.model_validate(response.data[0]) # Use model_validate
        return None

    async def get_by_host_user_id(self, host_user_id: str, *, active_only: bool = False) -> List[GameSession]:
        """Retrieve game sessions created by a specific user."""
        host_user_id_str = ensure_uuid(host_user_id)
        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("host_user_id", host_user_id_str)
        )
        if active_only:
            query = query.in_("status", [GameStatus.ACTIVE.value, GameStatus.PENDING.value])
        response = await self._execute_query(query)
        return [self.model.model_validate(item) for item in response.data] # Use model_validate

    async def get_active_games(self) -> List[GameSession]:
        """Retrieve all active game sessions."""
        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("status", GameStatus.ACTIVE.value)
        )
        response = await self._execute_query(query)
        return [self.model.model_validate(item) for item in response.data] # Use model_validate

    async def update_game_status(self, game_id: str, status: GameStatus) -> Optional[GameSession]:
        """Update the status of a game session."""
        game_id_str = ensure_uuid(game_id)

        # --- FIX: Explicitly convert datetime to ISO string ---
        now_iso = datetime.utcnow().isoformat() + "Z" # Add Z for UTC
        update_data = {
            "status": status.value,
            "updated_at": now_iso # Use the ISO string directly
        }
        # --- END FIX ---

        query = self.db.table(self.table_name).update(update_data).eq("id", game_id_str)
        await self._execute_query(query) # This should now work

        # Fetch and return the updated object
        return await self.get_by_id(game_id) # get_by_id uses model_validate