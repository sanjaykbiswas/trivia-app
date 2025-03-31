# backend/src/repositories/user_pack_history_repository.py
import uuid
from typing import List, Optional
from supabase import AsyncClient
from datetime import datetime

from ..models.user_pack_history import UserPackHistory, UserPackHistoryCreate, UserPackHistoryUpdate
from .base_repository_impl import BaseRepositoryImpl
from ..utils import ensure_uuid

class UserPackHistoryRepository(BaseRepositoryImpl[UserPackHistory, UserPackHistoryCreate, UserPackHistoryUpdate, str]):
    """
    Repository for managing UserPackHistory data in Supabase.
    """
    def __init__(self, db: AsyncClient):
        super().__init__(model=UserPackHistory, db=db, table_name="user_pack_history") # Table name: "user_pack_history"

    # --- Custom UserPackHistory-specific methods ---

    async def get_by_user_id(self, user_id: str, *, skip: int = 0, limit: int = 100) -> List[UserPackHistory]:
        """Retrieve history entries for a specific user."""
        # Ensure user_id is a valid UUID string
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
        return [self.model.parse_obj(item) for item in response.data]

    async def get_by_pack_id(self, pack_id: str, *, skip: int = 0, limit: int = 100) -> List[UserPackHistory]:
        """Retrieve history entries for a specific pack."""
        # Ensure pack_id is a valid UUID string
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
        return [self.model.parse_obj(item) for item in response.data]

    async def get_by_user_and_pack(self, user_id: str, pack_id: str) -> Optional[UserPackHistory]:
        """Retrieve the specific history entry for a user and pack."""
        # Ensure UUIDs are valid UUID strings
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
            return self.model.parse_obj(response.data[0])
        return None

    async def increment_play_count(self, user_id: str, pack_id: str) -> Optional[UserPackHistory]:
        """Finds existing history or creates one, increments play count and updates timestamp."""
        # Ensure UUIDs are valid UUID strings
        user_id_str = ensure_uuid(user_id)
        pack_id_str = ensure_uuid(pack_id)
        
        existing = await self.get_by_user_and_pack(user_id_str, pack_id_str)
        now = datetime.utcnow()

        if existing:
            # Update existing entry
            update_data = {
                "play_count": existing.play_count + 1,
                "last_played_at": now.isoformat() # Ensure ISO format string for Supabase
            }
            query = self.db.table(self.table_name).update(update_data).eq("id", existing.id)
            await self._execute_query(query)
            
            # Fetch and return the updated record
            return await self.get_by_id(existing.id)
        else:
            # Create new entry with the proper create schema
            new_history = UserPackHistoryCreate(
                user_id=user_id_str,
                pack_id=pack_id_str,
                play_count=1,
                last_played_at=now
            )
            return await self.create(obj_in=new_history)