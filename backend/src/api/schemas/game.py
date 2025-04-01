# backend/src/api/schemas/game.py
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

from ...models.game_session import GameStatus

class GameSessionCreateRequest(BaseModel):
    """Request schema for creating a new game session."""
    pack_id: str = Field(..., description="ID of the pack to use for the game")
    max_participants: int = Field(10, description="Maximum number of participants allowed", ge=2, le=50)
    question_count: int = Field(10, description="Number of questions to include in the game", ge=1, le=75)
    time_limit_seconds: int = Field(0, description="Time limit per question in seconds (0 for no limit)", ge=0)

class GameSessionJoinRequest(BaseModel):
    """Request schema for joining a game session."""
    game_code: str = Field(..., description="Code for the game to join")
    display_name: str = Field(..., description="Display name to use in the game")

class GameSessionSubmitAnswerRequest(BaseModel):
    """Request schema for submitting an answer."""
    question_index: int = Field(..., description="Index of the question being answered", ge=0)
    answer: str = Field(..., description="Answer submitted by the participant")

class ParticipantResponse(BaseModel):
    """Response schema for a game participant."""
    id: str
    display_name: str
    score: int
    is_host: bool

class GameSessionResponse(BaseModel):
    """Response schema for a game session."""
    id: str
    code: str
    status: GameStatus
    pack_id: str
    max_participants: int
    question_count: int
    time_limit_seconds: int
    current_question_index: int
    participant_count: int = Field(..., description="Current number of participants")
    is_host: bool = Field(..., description="Whether the current user is the host")
    created_at: datetime

class GameSessionListResponse(BaseModel):
    """Response schema for listing game sessions."""
    total: int
    games: List[Dict[str, Any]]

class GameQuestionResponse(BaseModel):
    """Response schema for a game question."""
    index: int
    question_text: str
    options: List[str]
    time_limit: int

class QuestionResultResponse(BaseModel):
    """Response schema for question result."""
    is_correct: bool
    correct_answer: str
    score: int
    total_score: int

class GameResultsResponse(BaseModel):
    """Response schema for game results."""
    game_id: str
    game_code: str
    status: GameStatus
    participants: List[Dict[str, Any]]
    questions: List[Dict[str, Any]]
    total_questions: int
    completed_at: str