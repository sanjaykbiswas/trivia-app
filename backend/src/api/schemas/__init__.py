# backend/src/api/schemas/__init__.py
"""
API schemas for request and response models.

This package contains Pydantic models that define the structure
of request bodies and response payloads for the API.
"""

# Import schemas from individual files
from .pack import PackCreateRequest, PackResponse, PackListResponse
from .topic import TopicGenerateRequest, TopicAddRequest, TopicResponse
from .difficulty import DifficultyDescription, DifficultyGenerateRequest, DifficultyUpdateRequest, DifficultyResponse
from .question import (
    QuestionGenerateRequest, SeedQuestionRequest, SeedQuestionTextRequest,
    QuestionResponse, QuestionsResponse, SeedQuestionsResponse,
    CustomInstructionsGenerateRequest, CustomInstructionsInputRequest, CustomInstructionsResponse,
    # --- ADDED/MODIFIED IMPORTS for batch generation ---
    DifficultyConfig, # Added this new schema
    TopicQuestionConfig, # This schema was modified
    BatchQuestionGenerateRequest, # This schema uses the modified TopicQuestionConfig
    BatchQuestionGenerateResponse
)
from .game import (
    GameSessionCreateRequest, GameSessionJoinRequest, GameSessionSubmitAnswerRequest,
    ParticipantResponse, GameSessionResponse, GameSessionListResponse,
    GameQuestionResponse, QuestionResultResponse, GameResultsResponse, GameStartResponse
)
from .user import (
    UserCreateRequest, UserResponse, UserUpdateRequest,
    UserLoginRequest, UserAuthRequest, UserConvertRequest
)

# Define what gets imported when using 'from .schemas import *'
# Also makes these schemas available directly under 'schemas' namespace
__all__ = [
    # Pack schemas
    "PackCreateRequest",
    "PackResponse",
    "PackListResponse",

    # Topic schemas
    "TopicGenerateRequest",
    "TopicAddRequest",
    "TopicResponse",

    # Difficulty schemas
    "DifficultyDescription",
    "DifficultyGenerateRequest",
    "DifficultyUpdateRequest",
    "DifficultyResponse",

    # Question schemas
    "QuestionGenerateRequest",
    "SeedQuestionRequest",
    "SeedQuestionTextRequest",
    "QuestionResponse",
    "QuestionsResponse",
    "SeedQuestionsResponse",
    "CustomInstructionsGenerateRequest",
    "CustomInstructionsInputRequest",
    "CustomInstructionsResponse",
    # --- ADDED/MODIFIED SCHEMAS for batch generation ---
    "DifficultyConfig", # Added export
    "TopicQuestionConfig", # Keep export (modified)
    "BatchQuestionGenerateRequest", # Keep export
    "BatchQuestionGenerateResponse", # Keep export

    # Game schemas
    "GameSessionCreateRequest",
    "GameSessionJoinRequest",
    "GameSessionSubmitAnswerRequest",
    "ParticipantResponse",
    "GameSessionResponse",
    "GameSessionListResponse",
    "GameQuestionResponse",
    "QuestionResultResponse",
    "GameResultsResponse",
    "GameStartResponse",

    # User schemas
    "UserCreateRequest",
    "UserResponse",
    "UserUpdateRequest",
    "UserLoginRequest",
    "UserAuthRequest",
    "UserConvertRequest",
]