# backend/src/repositories/user_question_history_repository.py
import uuid
import logging # Import logging
from typing import List, Optional, Set # Added Set
from supabase import AsyncClient

from ..models.user_question_history import UserQuestionHistory, UserQuestionHistoryCreate, UserQuestionHistoryUpdate
from .base_repository_impl import BaseRepositoryImpl
from ..utils import ensure_uuid

# Configure logger
logger = logging.getLogger(__name__)

class UserQuestionHistoryRepository(BaseRepositoryImpl[UserQuestionHistory, UserQuestionHistoryCreate, UserQuestionHistoryUpdate, str]):
    """
    Repository for managing UserQuestionHistory data in Supabase.
    """
    def __init__(self, db: AsyncClient):
        super().__init__(model=UserQuestionHistory, db=db, table_name="user_question_history") # Table name: "user_question_history"

    # --- Custom UserQuestionHistory-specific methods ---

    async def get_by_user_id(self, user_id: str, *, skip: int = 0, limit: int = 100) -> List[UserQuestionHistory]:
        """Retrieve history entries for a specific user."""
        # Ensure user_id is a valid UUID string
        user_id_str = ensure_uuid(user_id)

        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("user_id", user_id_str)
            .order("created_at", desc=True) # Optional: order by date
            .offset(skip)
            .limit(limit)
        )
        response = await self._execute_query(query)
        return [self.model.model_validate(item) for item in response.data] # Use model_validate

    async def get_by_question_id(self, question_id: str, *, skip: int = 0, limit: int = 100) -> List[UserQuestionHistory]:
        """Retrieve history entries for a specific question."""
        # Ensure question_id is a valid UUID string
        question_id_str = ensure_uuid(question_id)

        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("question_id", question_id_str)
            .order("created_at", desc=True)
            .offset(skip)
            .limit(limit)
        )
        response = await self._execute_query(query)
        return [self.model.model_validate(item) for item in response.data] # Use model_validate

    async def get_by_user_and_question(self, user_id: str, question_id: str) -> List[UserQuestionHistory]:
        """Retrieve all history entries for a specific user and question."""
        # Ensure UUIDs are valid UUID strings
        user_id_str = ensure_uuid(user_id)
        question_id_str = ensure_uuid(question_id)

        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("user_id", user_id_str)
            .eq("question_id", question_id_str)
            .order("created_at", desc=True)
        )
        response = await self._execute_query(query)
        return [self.model.model_validate(item) for item in response.data] # Use model_validate

    # --- NEW METHOD for efficient checking ---
    async def get_seen_question_ids_for_users(
        self, user_ids: List[str], question_ids: List[str]
    ) -> Set[str]:
        """
        Retrieve the set of question IDs that have been seen by any of the specified users.
        Filters by the provided question_ids to limit the search scope.

        Args:
            user_ids: List of user IDs to check history for.
            question_ids: List of question IDs to consider.

        Returns:
            A set containing the string representations of question IDs seen by any user.
        """
        if not user_ids or not question_ids:
            return set() # No need to query if either list is empty

        # Ensure UUIDs are strings
        user_ids_str = [ensure_uuid(uid) for uid in user_ids]
        question_ids_str = [ensure_uuid(qid) for qid in question_ids]

        try:
            # Query for distinct question_ids seen by any of the users within the question pool
            query = (
                self.db.table(self.table_name)
                .select("question_id", count="exact") # Fetch only question_id, count for potential pagination (though not used here)
                .in_("user_id", user_ids_str)
                .in_("question_id", question_ids_str)
                # Supabase Python client might not directly support DISTINCT in select easily.
                # We fetch all matching question_ids and dedup in Python using a set.
            )
            response = await self._execute_query(query)

            # Extract unique question IDs from the response data
            seen_ids = {item["question_id"] for item in response.data if "question_id" in item}
            return seen_ids

        except Exception as e:
            logger.error(f"Error fetching seen question IDs for users {user_ids_str}: {e}", exc_info=True)
            # Return empty set on error to avoid blocking game start, but log it.
            return set()
    # --- END NEW METHOD ---