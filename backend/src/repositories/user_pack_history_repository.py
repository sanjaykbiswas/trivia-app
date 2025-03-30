# backend/src/repositories/user_pack_history_repository.py
import uuid
from typing import List, Optional
from supabase import Client  # Updated import
from datetime import datetime

from ..models.user_pack_history import UserPackHistory, UserPackHistoryCreate, UserPackHistoryUpdate
from .base_repository_impl import BaseRepositoryImpl

class UserPackHistoryRepository(BaseRepositoryImpl[UserPackHistory, UserPackHistoryCreate, UserPackHistoryUpdate, uuid.UUID]):
    """
    Repository for managing UserPackHistory data in Supabase.
    """
    def __init__(self, db: Client):  # Updated type annotation
        super().__init__(model=UserPackHistory, db=db, table_name="user_pack_history") # Table name: "user_pack_history"

    # --- Custom UserPackHistory-specific methods ---

    async def get_by_user_id(self, user_id: uuid.UUID, *, skip: int = 0, limit: int = 100) -> List[UserPackHistory]:
        """Retrieve history entries for a specific user."""
        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("user_id", str(user_id))
            .order("last_played_at", desc=True) # Order by most recently played
            .offset(skip)
            .limit(limit)
        )
        response = await self._execute_query(query)
        return [self.model.parse_obj(item) for item in response.data]

    async def get_by_pack_id(self, pack_id: uuid.UUID, *, skip: int = 0, limit: int = 100) -> List[UserPackHistory]:
        """Retrieve history entries for a specific pack."""
        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("pack_id", str(pack_id))
            .order("last_played_at", desc=True)
            .offset(skip)
            .limit(limit)
        )
        response = await self._execute_query(query)
        return [self.model.parse_obj(item) for item in response.data]

    async def get_by_user_and_pack(self, user_id: uuid.UUID, pack_id: uuid.UUID) -> Optional[UserPackHistory]:
        """Retrieve the specific history entry for a user and pack."""
        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("user_id", str(user_id))
            .eq("pack_id", str(pack_id))
            .limit(1) # Should be unique combination
        )
        response = await self._execute_query(query)
        if response.data:
            return self.model.parse_obj(response.data[0])
        return None

    async def increment_play_count(self, user_id: uuid.UUID, pack_id: uuid.UUID) -> Optional[UserPackHistory]:
        """Finds existing history or creates one, increments play count and updates timestamp."""
        existing = await self.get_by_user_and_pack(user_id, pack_id)
        now = datetime.utcnow()

        if existing:
            # Update existing entry
            update_data = {
                "play_count": existing.play_count + 1,
                "last_played_at": now.isoformat() # Ensure ISO format string for Supabase
            }
            query = self.db.table(self.table_name).update(update_data).eq("id", str(existing.id)).returning('representation')
            response = await self._execute_query(query)
            if response.data:
                return self.model.parse_obj(response.data[0])
            return None # Update failed?
        else:
            # Create new entry with the proper create schema
            new_history = UserPackHistoryCreate(
                user_id=user_id,
                pack_id=pack_id,
                play_count=1,
                last_played_at=now
            )
            return await self.create(obj_in=new_history)