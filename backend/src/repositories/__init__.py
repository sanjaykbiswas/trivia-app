# Update to backend/src/repositories/__init__.py
"""
Repositories module providing data access layer implementations.

Exports repository classes for interacting with the database via Supabase.
"""

from .base_repository import BaseRepository
from .user_repository import UserRepository
from .question_repository import QuestionRepository
from .incorrect_answers_repository import IncorrectAnswersRepository
from .pack_group_repository import PackGroupRepository
from .pack_repository import PackRepository
from .user_question_history_repository import UserQuestionHistoryRepository
from .user_pack_history_repository import UserPackHistoryRepository
from .pack_creation_data_repository import PackCreationDataRepository
# Add new game repositories
from .game_session_repository import GameSessionRepository
from .game_participant_repository import GameParticipantRepository
from .game_question_repository import GameQuestionRepository
# Add new topic repository
from .topic_repository import TopicRepository

__all__ = [
    "BaseRepository", # Exporting the base abstract class for type hinting
    "UserRepository",
    "QuestionRepository",
    "IncorrectAnswersRepository",
    "PackGroupRepository",
    "PackRepository",
    "UserQuestionHistoryRepository",
    "UserPackHistoryRepository",
    "PackCreationDataRepository",
    # Add new game repositories
    "GameSessionRepository",
    "GameParticipantRepository",
    "GameQuestionRepository",
    # Add new topic repository
    "TopicRepository",
]