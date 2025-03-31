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
    QuestionResponse, QuestionsResponse, SeedQuestionsResponse
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
]