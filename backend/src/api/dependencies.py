# backend/src/api/dependencies.py
from fastapi import Depends, Request
from supabase import AsyncClient

# Ensure repositories are imported FIRST
from ..repositories.pack_repository import PackRepository
from ..repositories.pack_creation_data_repository import PackCreationDataRepository
from ..repositories.question_repository import QuestionRepository
from ..repositories.incorrect_answers_repository import IncorrectAnswersRepository
from ..repositories.game_session_repository import GameSessionRepository
from ..repositories.game_participant_repository import GameParticipantRepository
from ..repositories.game_question_repository import GameQuestionRepository
from ..repositories.user_repository import UserRepository # Make sure this is imported

# Services
from ..services.pack_service import PackService
from ..services.topic_service import TopicService
from ..services.difficulty_service import DifficultyService
from ..services.question_service import QuestionService
from ..services.seed_question_service import SeedQuestionService
from ..services.incorrect_answer_service import IncorrectAnswerService
from ..services.game_service import GameService
from ..services.user_service import UserService


async def get_supabase_client(request: Request) -> AsyncClient:
    """
    Get Supabase client from request state.

    Args:
        request: FastAPI request object

    Returns:
        AsyncClient: Supabase client
    """
    return request.app.state.supabase

# --- Repository dependencies ---
async def get_pack_repository(
    supabase: AsyncClient = Depends(get_supabase_client)
) -> PackRepository:
    """Get PackRepository instance."""
    return PackRepository(supabase)

async def get_pack_creation_data_repository(
    supabase: AsyncClient = Depends(get_supabase_client)
) -> PackCreationDataRepository:
    """Get PackCreationDataRepository instance."""
    return PackCreationDataRepository(supabase)

async def get_question_repository(
    supabase: AsyncClient = Depends(get_supabase_client)
) -> QuestionRepository:
    """Get QuestionRepository instance."""
    return QuestionRepository(supabase)

async def get_incorrect_answers_repository(
    supabase: AsyncClient = Depends(get_supabase_client)
) -> IncorrectAnswersRepository:
    """Get IncorrectAnswersRepository instance."""
    return IncorrectAnswersRepository(supabase)

async def get_game_session_repository(
    supabase: AsyncClient = Depends(get_supabase_client)
) -> GameSessionRepository:
    """Get GameSessionRepository instance."""
    return GameSessionRepository(supabase)

async def get_game_participant_repository(
    supabase: AsyncClient = Depends(get_supabase_client)
) -> GameParticipantRepository:
    """Get GameParticipantRepository instance."""
    return GameParticipantRepository(supabase)

async def get_game_question_repository(
    supabase: AsyncClient = Depends(get_supabase_client)
) -> GameQuestionRepository:
    """Get GameQuestionRepository instance."""
    return GameQuestionRepository(supabase)

# Define get_user_repository before it's used by get_user_service
async def get_user_repository(
    supabase: AsyncClient = Depends(get_supabase_client)
) -> UserRepository:
    """Get UserRepository instance."""
    return UserRepository(supabase)

# --- Service dependencies ---
async def get_pack_service(
    pack_repository: PackRepository = Depends(get_pack_repository)
) -> PackService:
    """Get PackService instance."""
    return PackService(pack_repository=pack_repository)

async def get_topic_service(
    pack_creation_data_repository: PackCreationDataRepository = Depends(get_pack_creation_data_repository)
) -> TopicService:
    """Get TopicService instance."""
    return TopicService(pack_creation_data_repository=pack_creation_data_repository)

async def get_difficulty_service(
    pack_creation_data_repository: PackCreationDataRepository = Depends(get_pack_creation_data_repository)
) -> DifficultyService:
    """Get DifficultyService instance."""
    return DifficultyService(pack_creation_data_repository=pack_creation_data_repository)

async def get_question_service(
    question_repository: QuestionRepository = Depends(get_question_repository),
    pack_creation_data_repository: PackCreationDataRepository = Depends(get_pack_creation_data_repository),
    incorrect_answers_repository: IncorrectAnswersRepository = Depends(get_incorrect_answers_repository)
) -> QuestionService:
    """Get QuestionService instance."""
    return QuestionService(
        question_repository=question_repository,
        pack_creation_data_repository=pack_creation_data_repository,
        incorrect_answers_repository=incorrect_answers_repository
    )

async def get_seed_question_service(
    pack_creation_data_repository: PackCreationDataRepository = Depends(get_pack_creation_data_repository)
) -> SeedQuestionService:
    """Get SeedQuestionService instance."""
    return SeedQuestionService(pack_creation_data_repository=pack_creation_data_repository)

async def get_incorrect_answer_service(
    question_repository: QuestionRepository = Depends(get_question_repository),
    incorrect_answers_repository: IncorrectAnswersRepository = Depends(get_incorrect_answers_repository)
) -> IncorrectAnswerService:
    """Get IncorrectAnswerService instance."""
    return IncorrectAnswerService(
        question_repository=question_repository,
        incorrect_answers_repository=incorrect_answers_repository
    )

async def get_game_service(
    game_session_repository: GameSessionRepository = Depends(get_game_session_repository),
    game_participant_repository: GameParticipantRepository = Depends(get_game_participant_repository),
    game_question_repository: GameQuestionRepository = Depends(get_game_question_repository),
    question_repository: QuestionRepository = Depends(get_question_repository),
    incorrect_answers_repository: IncorrectAnswersRepository = Depends(get_incorrect_answers_repository)
) -> GameService:
    """Get GameService instance."""
    return GameService(
        game_session_repository=game_session_repository,
        game_participant_repository=game_participant_repository,
        game_question_repository=game_question_repository,
        question_repository=question_repository,
        incorrect_answers_repository=incorrect_answers_repository
    )

# Define get_user_service using the now-defined get_user_repository
async def get_user_service(
    user_repository: UserRepository = Depends(get_user_repository) # Correct dependency
) -> UserService:
    """Get UserService instance."""
    return UserService(user_repository=user_repository)