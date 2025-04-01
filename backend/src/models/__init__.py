# Update to backend/src/models/__init__.py
"""
Models module containing all data models for the Trivia application.

This package contains all Pydantic models used for data validation,
serialization, and representing database entities.
"""

from .base_schema import BaseCreateSchema, BaseUpdateSchema
from .question import Question, DifficultyLevel, QuestionCreate, QuestionUpdate
from .incorrect_answers import IncorrectAnswers, IncorrectAnswersCreate, IncorrectAnswersUpdate
from .pack_group import PackGroup, PackGroupCreate, PackGroupUpdate
from .pack import Pack, CreatorType, PackCreate, PackUpdate
from .user import User, UserCreate, UserUpdate
from .user_question_history import UserQuestionHistory, UserQuestionHistoryCreate, UserQuestionHistoryUpdate
from .user_pack_history import UserPackHistory, UserPackHistoryCreate, UserPackHistoryUpdate
from .pack_creation_data import PackCreationData, PackCreationDataCreate, PackCreationDataUpdate
# Add new game models
from .game_session import GameSession, GameSessionCreate, GameSessionUpdate, GameStatus
from .game_participant import GameParticipant, GameParticipantCreate, GameParticipantUpdate
from .game_question import GameQuestion, GameQuestionCreate, GameQuestionUpdate

__all__ = [
    # Base schemas
    'BaseCreateSchema',
    'BaseUpdateSchema',
    
    # Question models
    'Question',
    'DifficultyLevel',
    'QuestionCreate',
    'QuestionUpdate',
    
    # Incorrect answers models
    'IncorrectAnswers',
    'IncorrectAnswersCreate',
    'IncorrectAnswersUpdate',
    
    # Pack group models
    'PackGroup',
    'PackGroupCreate',
    'PackGroupUpdate',
    
    # Pack models
    'Pack',
    'CreatorType',
    'PackCreate',
    'PackUpdate',
    
    # User models
    'User',
    'UserCreate',
    'UserUpdate',
    
    # User question history models
    'UserQuestionHistory',
    'UserQuestionHistoryCreate',
    'UserQuestionHistoryUpdate',
    
    # User pack history models
    'UserPackHistory',
    'UserPackHistoryCreate',
    'UserPackHistoryUpdate',
    
    # Pack creation data models
    'PackCreationData',
    'PackCreationDataCreate',
    'PackCreationDataUpdate',
    
    # Game session models
    'GameSession',
    'GameSessionCreate',
    'GameSessionUpdate',
    'GameStatus',
    
    # Game participant models
    'GameParticipant',
    'GameParticipantCreate',
    'GameParticipantUpdate',
    
    # Game question models
    'GameQuestion',
    'GameQuestionCreate',
    'GameQuestionUpdate',
]