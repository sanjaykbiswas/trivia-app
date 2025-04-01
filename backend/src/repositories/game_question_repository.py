# backend/src/repositories/game_question_repository.py
import uuid
from typing import List, Optional, Dict
from datetime import datetime
from supabase import AsyncClient

from ..models.game_question import GameQuestion, GameQuestionCreate, GameQuestionUpdate
from .base_repository_impl import BaseRepositoryImpl
from ..utils import ensure_uuid

class GameQuestionRepository(BaseRepositoryImpl[GameQuestion, GameQuestionCreate, GameQuestionUpdate, str]):
    """
    Repository for managing GameQuestion data in Supabase.
    """
    def __init__(self, db: AsyncClient):
        super().__init__(model=GameQuestion, db=db, table_name="game_questions") # Table name: "game_questions"

    # --- Custom GameQuestion-specific methods ---

    async def get_by_game_session_id(self, game_session_id: str) -> List[GameQuestion]:
        """Retrieve all questions for a specific game session."""
        # Ensure game_session_id is a valid UUID string
        game_session_id_str = ensure_uuid(game_session_id)
        
        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("game_session_id", game_session_id_str)
            .order("question_index")
        )
        response = await self._execute_query(query)
        return [self.model.parse_obj(item) for item in response.data]

    async def get_by_game_session_and_index(self, game_session_id: str, question_index: int) -> Optional[GameQuestion]:
        """Retrieve a specific question by game session ID and question index."""
        # Ensure game_session_id is a valid UUID string
        game_session_id_str = ensure_uuid(game_session_id)
        
        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("game_session_id", game_session_id_str)
            .eq("question_index", question_index)
            .limit(1)
        )
        response = await self._execute_query(query)
        if response.data:
            return self.model.parse_obj(response.data[0])
        return None

    async def start_question(self, question_id: str) -> Optional[GameQuestion]:
        """Mark a question as started (set start_time)."""
        # Ensure question_id is a valid UUID string
        question_id_str = ensure_uuid(question_id)
        
        now = datetime.utcnow()
        update_data = {"start_time": now.isoformat()}
        
        query = self.db.table(self.table_name).update(update_data).eq("id", question_id_str)
        await self._execute_query(query)
        
        # Fetch and return the updated object
        return await self.get_by_id(question_id)

    async def end_question(self, question_id: str) -> Optional[GameQuestion]:
        """Mark a question as ended (set end_time)."""
        # Ensure question_id is a valid UUID string
        question_id_str = ensure_uuid(question_id)
        
        now = datetime.utcnow()
        update_data = {"end_time": now.isoformat()}
        
        query = self.db.table(self.table_name).update(update_data).eq("id", question_id_str)
        await self._execute_query(query)
        
        # Fetch and return the updated object
        return await self.get_by_id(question_id)

    async def record_participant_answer(
        self, 
        question_id: str, 
        participant_id: str, 
        answer: str
    ) -> Optional[GameQuestion]:
        """Record a participant's answer for a question."""
        # Ensure question_id is a valid UUID string
        question_id_str = ensure_uuid(question_id)
        
        # First, get the current question to access existing participant_answers
        current_question = await self.get_by_id(question_id_str)
        if not current_question:
            return None
            
        # Update the participant_answers dictionary
        participant_answers = dict(current_question.participant_answers)
        participant_answers[participant_id] = answer
        
        # Update in database
        update_data = {"participant_answers": participant_answers}
        query = self.db.table(self.table_name).update(update_data).eq("id", question_id_str)
        await self._execute_query(query)
        
        # Fetch and return the updated object
        return await self.get_by_id(question_id)

    async def record_participant_score(
        self, 
        question_id: str, 
        participant_id: str, 
        score: int
    ) -> Optional[GameQuestion]:
        """Record a participant's score for a question."""
        # Ensure question_id is a valid UUID string
        question_id_str = ensure_uuid(question_id)
        
        # First, get the current question to access existing participant_scores
        current_question = await self.get_by_id(question_id_str)
        if not current_question:
            return None
            
        # Update the participant_scores dictionary
        participant_scores = dict(current_question.participant_scores)
        participant_scores[participant_id] = score
        
        # Update in database
        update_data = {"participant_scores": participant_scores}
        query = self.db.table(self.table_name).update(update_data).eq("id", question_id_str)
        await self._execute_query(query)
        
        # Fetch and return the updated object
        return await self.get_by_id(question_id)