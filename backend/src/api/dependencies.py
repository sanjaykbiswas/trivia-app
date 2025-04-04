# backend/src/api/dependencies.py
from fastapi import Depends, Request
from supabase import AsyncClient

# --- WebSocket Manager Import ---
from ..websocket_manager import ConnectionManager # <<< ADDED
# --- End WebSocket Manager Import ---


# Ensure repositories are imported FIRST
from ..repositories.pack_repository import PackRepository
from ..repositories.question_repository import QuestionRepository
from ..repositories.incorrect_answers_repository import IncorrectAnswersRepository
from ..repositories.game_session_repository import GameSessionRepository
from ..repositories.game_participant_repository import GameParticipantRepository
from ..repositories.game_question_repository import GameQuestionRepository
from ..repositories.user_repository import UserRepository
from ..repositories.topic_repository import TopicRepository
from ..repositories.user_question_history_repository import UserQuestionHistoryRepository
from ..repositories.user_pack_history_repository import UserPackHistoryRepository


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
    # Ensure the client exists in state (initialized during lifespan)
    if not hasattr(request.app.state, 'supabase') or not request.app.state.supabase:
        raise RuntimeError("Supabase client not initialized or found in app state.")
    return request.app.state.supabase

# --- ADD Dependency for ConnectionManager ---
async def get_connection_manager(request: Request) -> ConnectionManager:
    """Get the shared ConnectionManager instance from request state."""
    if not hasattr(request.app.state, 'connection_manager') or not request.app.state.connection_manager:
        # This should theoretically not happen if lifespan runs correctly
        raise RuntimeError("ConnectionManager not initialized or found in app state.")
    return request.app.state.connection_manager
# --- END ADD ---

# --- Repository dependencies (Unchanged) ---
async def get_pack_repository(
    supabase: AsyncClient = Depends(get_supabase_client)
) -> PackRepository:
    return PackRepository(supabase)

async def get_question_repository(
    supabase: AsyncClient = Depends(get_supabase_client)
) -> QuestionRepository:
    return QuestionRepository(supabase)

async def get_incorrect_answers_repository(
    supabase: AsyncClient = Depends(get_supabase_client)
) -> IncorrectAnswersRepository:
    return IncorrectAnswersRepository(supabase)

async def get_game_session_repository(
    supabase: AsyncClient = Depends(get_supabase_client)
) -> GameSessionRepository:
    return GameSessionRepository(supabase)

async def get_game_participant_repository(
    supabase: AsyncClient = Depends(get_supabase_client)
) -> GameParticipantRepository:
    return GameParticipantRepository(supabase)

async def get_game_question_repository(
    supabase: AsyncClient = Depends(get_supabase_client)
) -> GameQuestionRepository:
    return GameQuestionRepository(supabase)

async def get_user_repository(
    supabase: AsyncClient = Depends(get_supabase_client)
) -> UserRepository:
    return UserRepository(supabase)

async def get_topic_repository(
    supabase: AsyncClient = Depends(get_supabase_client)
) -> TopicRepository:
    return TopicRepository(supabase)

async def get_user_question_history_repository(
    supabase: AsyncClient = Depends(get_supabase_client)
) -> UserQuestionHistoryRepository:
    return UserQuestionHistoryRepository(supabase)

async def get_user_pack_history_repository(
    supabase: AsyncClient = Depends(get_supabase_client)
) -> UserPackHistoryRepository:
    return UserPackHistoryRepository(supabase)


# --- Service dependencies (Modified to inject ConnectionManager) ---

# Pack, Topic, Difficulty, Seed, Question, IncorrectAnswer services remain unchanged
# as they don't directly interact with WebSockets in this design.

async def get_pack_service(
    pack_repository: PackRepository = Depends(get_pack_repository)
) -> PackService:
    return PackService(pack_repository=pack_repository)

async def get_topic_service(
    topic_repository: TopicRepository = Depends(get_topic_repository)
) -> TopicService:
    return TopicService(topic_repository=topic_repository)

async def get_difficulty_service(
    topic_service: TopicService = Depends(get_topic_service),
    pack_repository: PackRepository = Depends(get_pack_repository)
) -> DifficultyService:
    return DifficultyService(
        topic_service=topic_service,
        pack_repository=pack_repository
    )

async def get_seed_question_service(
    pack_repository: PackRepository = Depends(get_pack_repository),
    topic_repository: TopicRepository = Depends(get_topic_repository)
) -> SeedQuestionService:
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
    return IncorrectAnswerService(
        question_repository=question_repository,
        incorrect_answers_repository=incorrect_answers_repository
    )

# --- MODIFIED get_user_service ---
async def get_user_service(
    user_repository: UserRepository = Depends(get_user_repository),
    game_participant_repository: GameParticipantRepository = Depends(get_game_participant_repository),
    game_session_repository: GameSessionRepository = Depends(get_game_session_repository),
    connection_manager: ConnectionManager = Depends(get_connection_manager) # <<< ADDED
) -> UserService:
    return UserService(
        user_repository=user_repository,
        game_participant_repository=game_participant_repository,
        game_session_repository=game_session_repository,
        connection_manager=connection_manager # <<< ADDED
    )
# --- END MODIFIED get_user_service ---

# --- MODIFIED get_game_service ---
async def get_game_service(
    game_session_repository: GameSessionRepository = Depends(get_game_session_repository),
    game_participant_repository: GameParticipantRepository = Depends(get_game_participant_repository),
    game_question_repository: GameQuestionRepository = Depends(get_game_question_repository),
    question_repository: QuestionRepository = Depends(get_question_repository),
    incorrect_answers_repository: IncorrectAnswersRepository = Depends(get_incorrect_answers_repository),
    user_repository: UserRepository = Depends(get_user_repository),
    user_question_history_repository: UserQuestionHistoryRepository = Depends(get_user_question_history_repository),
    user_pack_history_repository: UserPackHistoryRepository = Depends(get_user_pack_history_repository),
    connection_manager: ConnectionManager = Depends(get_connection_manager) # <<< ADDED
) -> GameService:
    """Get GameService instance."""
    return GameService(
        game_session_repository=game_session_repository,
        game_participant_repository=game_participant_repository,
        game_question_repository=game_question_repository,
        question_repository=question_repository,
        incorrect_answers_repository=incorrect_answers_repository,
        user_repository=user_repository,
        user_question_history_repository=user_question_history_repository,
        user_pack_history_repository=user_pack_history_repository,
        connection_manager=connection_manager # <<< ADDED
    )
# --- END MODIFIED get_game_service ---