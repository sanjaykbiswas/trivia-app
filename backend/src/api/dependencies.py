# backend/src/api/dependencies.py
from fastapi import Depends, Request
from supabase import AsyncClient

# Ensure repositories are imported FIRST
from ..repositories.pack_repository import PackRepository
from ..repositories.question_repository import QuestionRepository
from ..repositories.incorrect_answers_repository import IncorrectAnswersRepository
from ..repositories.game_session_repository import GameSessionRepository
from ..repositories.game_participant_repository import GameParticipantRepository
from ..repositories.game_question_repository import GameQuestionRepository
from ..repositories.user_repository import UserRepository # Keep UserRepository
from ..repositories.topic_repository import TopicRepository

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
    """Get Supabase client from request state."""
    return request.app.state.supabase

# --- Repository dependencies ---
async def get_pack_repository(
    supabase: AsyncClient = Depends(get_supabase_client)
) -> PackRepository:
    """Get PackRepository instance."""
    return PackRepository(supabase)

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

async def get_user_repository(
    supabase: AsyncClient = Depends(get_supabase_client)
) -> UserRepository:
    """Get UserRepository instance."""
    return UserRepository(supabase) # Keep this

async def get_topic_repository(
    supabase: AsyncClient = Depends(get_supabase_client)
) -> TopicRepository:
    """Get TopicRepository instance."""
    return TopicRepository(supabase)

# --- Service dependencies ---
async def get_pack_service(
    pack_repository: PackRepository = Depends(get_pack_repository)
) -> PackService:
    """Get PackService instance."""
    return PackService(pack_repository=pack_repository)

async def get_topic_service(
    topic_repository: TopicRepository = Depends(get_topic_repository)
) -> TopicService:
    """Get TopicService instance."""
    return TopicService(topic_repository=topic_repository)

async def get_difficulty_service(
    topic_service: TopicService = Depends(get_topic_service),
    pack_repository: PackRepository = Depends(get_pack_repository)
) -> DifficultyService:
    """Get DifficultyService instance."""
    return DifficultyService(
        topic_service=topic_service,
        pack_repository=pack_repository
    )

async def get_seed_question_service(
    pack_repository: PackRepository = Depends(get_pack_repository),
    topic_repository: TopicRepository = Depends(get_topic_repository)
) -> SeedQuestionService:
    """Get SeedQuestionService instance."""
    return SeedQuestionService(
        pack_repository=pack_repository,
        topic_repository=topic_repository
        )

async def get_question_service(
    question_repository: QuestionRepository = Depends(get_question_repository),
    pack_repository: PackRepository = Depends(get_pack_repository),
    topic_repository: TopicRepository = Depends(get_topic_repository),
    seed_question_service: SeedQuestionService = Depends(get_seed_question_service)
) -> QuestionService:
    """Get QuestionService instance."""
    return QuestionService(
        question_repository=question_repository,
        topic_repository=topic_repository,
        pack_repository=pack_repository,
        seed_question_service=seed_question_service
    )

async def get_incorrect_answer_service(
    question_repository: QuestionRepository = Depends(get_question_repository),
    incorrect_answers_repository: IncorrectAnswersRepository = Depends(get_incorrect_answers_repository)
) -> IncorrectAnswerService:
    """Get IncorrectAnswerService instance."""
    return IncorrectAnswerService(
        question_repository=question_repository,
        incorrect_answers_repository=incorrect_answers_repository
    )

# --- MODIFIED get_user_service ---
async def get_user_service(
    user_repository: UserRepository = Depends(get_user_repository),
    game_participant_repository: GameParticipantRepository = Depends(get_game_participant_repository), # <<< ADDED
    game_session_repository: GameSessionRepository = Depends(get_game_session_repository) # <<< ADDED
) -> UserService:
    """Get UserService instance."""
    return UserService(
        user_repository=user_repository,
        game_participant_repository=game_participant_repository, # <<< ADDED
        game_session_repository=game_session_repository # <<< ADDED
    )
# --- END MODIFIED get_user_service ---

async def get_game_service(
    game_session_repository: GameSessionRepository = Depends(get_game_session_repository),
    game_participant_repository: GameParticipantRepository = Depends(get_game_participant_repository),
    game_question_repository: GameQuestionRepository = Depends(get_game_question_repository),
    question_repository: QuestionRepository = Depends(get_question_repository),
    incorrect_answers_repository: IncorrectAnswersRepository = Depends(get_incorrect_answers_repository),
    user_repository: UserRepository = Depends(get_user_repository)
) -> GameService:
    """Get GameService instance."""
    return GameService(
        game_session_repository=game_session_repository,
        game_participant_repository=game_participant_repository,
        game_question_repository=game_question_repository,
        question_repository=question_repository,
        incorrect_answers_repository=incorrect_answers_repository,
        user_repository=user_repository
    )