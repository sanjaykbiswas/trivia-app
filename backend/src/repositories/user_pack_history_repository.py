# backend/src/repositories/user_pack_history_repository.py
import uuid
import logging # Import logging
from typing import List, Optional
from supabase import AsyncClient
from datetime import datetime, timezone # Import timezone

from ..models.user_pack_history import UserPackHistory, UserPackHistoryCreate, UserPackHistoryUpdate
from .base_repository_impl import BaseRepositoryImpl
from ..utils import ensure_uuid

# Configure logger
logger = logging.getLogger(__name__)

class UserPackHistoryRepository(BaseRepositoryImpl[UserPackHistory, UserPackHistoryCreate, UserPackHistoryUpdate, str]):
    """
    Repository for managing UserPackHistory data in Supabase.
    """
    def __init__(self, db: AsyncClient):
        super().__init__(model=UserPackHistory, db=db, table_name="user_pack_history") # Table name: "user_pack_history"

    # --- Custom UserPackHistory-specific methods ---

    async def get_by_user_id(self, user_id: str, *, skip: int = 0, limit: int = 100) -> List[UserPackHistory]:
        """Retrieve history entries for a specific user."""
        user_id_str = ensure_uuid(user_id)

        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("user_id", user_id_str)
            .order("last_played_at", desc=True) # Order by most recently played
            .offset(skip)
            .limit(limit)
        )
        response = await self._execute_query(query)
        return [self.model.model_validate(item) for item in response.data] # Use model_validate

    async def get_by_pack_id(self, pack_id: str, *, skip: int = 0, limit: int = 100) -> List[UserPackHistory]:
        """Retrieve history entries for a specific pack."""
        pack_id_str = ensure_uuid(pack_id)

        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("pack_id", pack_id_str)
            .order("last_played_at", desc=True)
            .offset(skip)
            .limit(limit)
        )
        response = await self._execute_query(query)
        return [self.model.model_validate(item) for item in response.data] # Use model_validate

    async def get_by_user_and_pack(self, user_id: str, pack_id: str) -> Optional[UserPackHistory]:
        """Retrieve the specific history entry for a user and pack."""
        user_id_str = ensure_uuid(user_id)
        pack_id_str = ensure_uuid(pack_id)

        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("user_id", user_id_str)
            .eq("pack_id", pack_id_str)
            .limit(1) # Should be unique combination
        )
        response = await self._execute_query(query)
        if response.data:
            return self.model.model_validate(response.data[0]) # Use model_validate
        return None

    # --- MODIFIED: increment_play_count ---
    async def increment_play_count(self, user_id: str, pack_id: str) -> Optional[UserPackHistory]:
        """
        Finds existing history or creates one, increments play count and updates timestamp.
        Returns the updated/created history record.
        """
        user_id_str = ensure_uuid(user_id)
        pack_id_str = ensure_uuid(pack_id)

        try:
            existing = await self.get_by_user_and_pack(user_id_str, pack_id_str)
            now_utc = datetime.now(timezone.utc)

            if existing:
                # Update existing entry
                updated_play_count = existing.play_count + 1
                update_data = UserPackHistoryUpdate(
                    play_count=updated_play_count,
                    last_played_at=now_utc # Pass datetime object
                )
                # Ensure ID is passed as string
                updated_record = await self.update(id=str(existing.id), obj_in=update_data)
                if updated_record:
                    logger.debug(f"Incremented play count for user {user_id_str} on pack {pack_id_str}")
                else:
                    logger.error(f"Failed to update pack history for user {user_id_str}, pack {pack_id_str}")
                return updated_record
            else:
                # Create new entry with the proper create schema
                new_history_data = UserPackHistoryCreate(
                    user_id=user_id_str,
                    pack_id=pack_id_str,
                    play_count=1,
                    last_played_at=now_utc # Pass datetime object
                )
                created_record = await self.create(obj_in=new_history_data)
                if created_record:
                     logger.info(f"Created new pack history for user {user_id_str} on pack {pack_id_str}")
                else:
                     logger.error(f"Failed to create pack history for user {user_id_str}, pack {pack_id_str}")
                return created_record
        except Exception as e:
            logger.error(f"Error incrementing play count for user {user_id_str}, pack {pack_id_str}: {e}", exc_info=True)
            return None # Return None on error
    # --- END MODIFIED: increment_play_count ---