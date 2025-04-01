# backend/src/api/schemas/__init__.py
"""
API schemas for request and response models.

This package contains Pydantic models that define the structure
of request bodies and response payloads for the API.
"""

from .pack import PackCreateRequest, PackResponse, PackListResponse
from .topic import TopicGenerateRequest, TopicAddRequest, TopicResponse
from .difficulty import DifficultyDescription, DifficultyGenerateRequest, DifficultyUpdateRequest, DifficultyResponse
from .question import (
    QuestionGenerateRequest, SeedQuestionRequest, SeedQuestionTextRequest,
    QuestionResponse, QuestionsResponse, SeedQuestionsResponse,
    CustomInstructionsGenerateRequest, CustomInstructionsInputRequest, CustomInstructionsResponse
)
from .game import (
    GameSessionCreateRequest, GameSessionJoinRequest, GameSessionSubmitAnswerRequest,
    ParticipantResponse, GameSessionResponse, GameSessionListResponse,
    GameQuestionResponse, QuestionResultResponse, GameResultsResponse
)

from .user import (
    UserCreateRequest, UserResponse, UserUpdateRequest,
    UserLoginRequest, UserAuthRequest, UserConvertRequest
)

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

    # User schemas
    "UserCreateRequest",
    "UserResponse",
    "UserUpdateRequest",
    "UserLoginRequest",
    "UserAuthRequest",
    "UserConvertRequest",
]