# backend/src/api/schemas/game.py
# --- START OF FULL MODIFIED FILE ---
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

# Import the enum from the correct location
from ...models.game_session import GameStatus

class GameSessionCreateRequest(BaseModel):
    """Request schema for creating a new game session."""
    pack_id: str = Field(..., description="ID of the pack to use for the game")
    max_participants: int = Field(10, description="Maximum number of participants allowed", ge=1, le=50)
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
    status: GameStatus # Use enum
    pack_id: str
    # --- ADDED host_user_id ---
    host_user_id: str = Field(..., description="ID of the user who created/hosts the game")
    # --- END ADDED host_user_id ---
    max_participants: int
    question_count: int
    time_limit_seconds: int
    current_question_index: int
    participant_count: int = Field(..., description="Current number of participants")
    is_host: bool = Field(..., description="Whether the current user making the request is the host") # Clarified description
    created_at: datetime

    class Config:
        from_attributes = True
        use_enum_values = True

class GameSessionListResponse(BaseModel):
    """Response schema for listing game sessions."""
    total: int
    games: List[Dict[str, Any]]

# Renamed GameQuestionInfo -> ApiGameQuestionInfo to avoid frontend naming conflicts potentially
class ApiGameQuestionInfo(BaseModel):
    """Schema for the current question info returned on game start or next question."""
    index: int
    question_text: str
    options: List[str]
    time_limit: int

class GameStartResponse(BaseModel):
    """Response schema for the start_game endpoint."""
    status: GameStatus
    current_question: ApiGameQuestionInfo

    class Config:
        from_attributes = True
        use_enum_values = True

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
    completed_at: datetime

    class Config:
        from_attributes = True
        use_enum_values = True

# --- NEW SCHEMAS FOR /play-questions Endpoint ---
class GamePlayQuestionResponse(BaseModel):
    """Schema for a single question served during gameplay."""
    index: int
    question_id: str
    question_text: str
    options: List[str]
    correct_answer_id: str
    time_limit: int

    class Config:
        from_attributes = True

class GamePlayQuestionListResponse(BaseModel):
    """Response schema for the list of questions for gameplay."""
    game_id: str
    questions: List[GamePlayQuestionResponse]
    total_questions: int
# --- END NEW SCHEMAS ---
# --- END OF FULL MODIFIED FILE ---