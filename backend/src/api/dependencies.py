from fastapi import Depends, Request
from supabase import AsyncClient

from ..repositories.pack_repository import PackRepository
from ..repositories.pack_creation_data_repository import PackCreationDataRepository
from ..repositories.question_repository import QuestionRepository
from ..repositories.incorrect_answers_repository import IncorrectAnswersRepository

from ..services.pack_service import PackService
from ..services.topic_service import TopicService
from ..services.difficulty_service import DifficultyService
from ..services.question_service import QuestionService
from ..services.seed_question_service import SeedQuestionService

async def get_supabase_client(request: Request) -> AsyncClient:
    """
    Get Supabase client from request state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        AsyncClient: Supabase client
    """
    return request.app.state.supabase

# Repository dependencies
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

# Service dependencies
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
    pack_creation_data_repository: PackCreationDataRepository = Depends(get_pack_creation_data_repository)
) -> QuestionService:
    """Get QuestionService instance."""
    return QuestionService(
        question_repository=question_repository,
        pack_creation_data_repository=pack_creation_data_repository
    )

async def get_seed_question_service(
    pack_creation_data_repository: PackCreationDataRepository = Depends(get_pack_creation_data_repository)
) -> SeedQuestionService:
    """Get SeedQuestionService instance."""
    return SeedQuestionService(pack_creation_data_repository=pack_creation_data_repository)