# backend/src/repositories/user_repository.py
import uuid
from typing import Optional, List
from supabase import AsyncClient

from ..models.user import User, UserCreate, UserUpdate
from .base_repository_impl import BaseRepositoryImpl
from ..utils import ensure_uuid

class UserRepository(BaseRepositoryImpl[User, UserCreate, UserUpdate, uuid.UUID]):
    """
    Repository for managing User data in Supabase.
    Inherits generic CRUD operations from BaseRepositoryImpl.
    """
    def __init__(self, db: AsyncClient):
        super().__init__(model=User, db=db, table_name="users") # Table name: "users"

    # --- Custom User-specific methods can be added here ---

    async def get_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user by their email address."""
        query = self.db.table(self.table_name).select("*").eq("email", email).limit(1)
        response = await self._execute_query(query)
        if response.data:
            return self.model.parse_obj(response.data[0])
        return None

    async def get_by_auth_details(self, auth_provider: str, auth_id: str) -> Optional[User]:
        """Retrieve a user by their authentication provider and ID."""
        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("auth_provider", auth_provider)
            .eq("auth_id", auth_id)
            .limit(1)
        )
        response = await self._execute_query(query)
        if response.data:
            return self.model.parse_obj(response.data[0])
        return None