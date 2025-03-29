# backend/src/main.py
from fastapi import FastAPI, Depends, Request
import supabase
import logging
import time
import sys
import os
from typing import List

# Add the src directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logging_config import setup_logging
from config.environment import Environment
from config.llm_config import LLMConfigFactory

# Repositories
from repositories.question_repository import QuestionRepository
from repositories.category_repository import CategoryRepository
from repositories.user_repository import UserRepository
from repositories.upload_repository import UploadRepository
from repositories.base_repository_impl import BaseRepositoryImpl

# Original Services
from services.question_service import QuestionService
from services.upload_service import UploadService
from services.user_service import UserService
from services.category_service import CategoryService

# Refactored Services
from services.refactored_question_service import RefactoredQuestionService
from services.refactored_upload_service import RefactoredUploadService
from services.refactored_user_service import RefactoredUserService
from services.refactored_category_service import RefactoredCategoryService

# Utilities
from utils.question_generator.generator import QuestionGenerator
from utils.question_generator.answer_generator import AnswerGenerator
from utils.question_generator.deduplicator import Deduplicator
from utils.supabase_actions import SupabaseActions
from utils.category_utils import CategoryUtils

# Controllers
from controllers.auth_controller import AuthController
from controllers.question_controller import QuestionController, MultiDifficultyRequest, MultiDifficultyResponse
from controllers.upload_controller import UploadController
from controllers.category_controller import CategoryController, CategoryResponse

# Feature flag to control whether to use refactored services
# This will make it easier to gradually transition to the refactored implementation
USE_REFACTORED_SERVICES = True  # Set to True to use refactored services, False to use original

# Set up logging
logger = setup_logging()

# Create FastAPI app
app = FastAPI(
    title="Trivia App API",
    description="""API for managing trivia questions and games. 
    
Features:
- Generate trivia questions in various categories and difficulty levels
- Generate questions with multiple difficulties concurrently
- Upload custom questions and answers
- Retrieve questions for trivia games
- Manage categories
    """,
    version="1.0.0"
)

# Add middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all API requests"""
    start_time = time.time()
    
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path} from {client_ip}")
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log response
    logger.info(f"Response: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.4f}s")
    
    return response

# Create singleton instances for shared services
def create_environment():
    """Create environment singleton"""
    return Environment()

def create_supabase_client():
    """Create Supabase client"""
    env = create_environment()
    return supabase.create_client(
        supabase_url=env.get("supabase_url"),
        supabase_key=env.get("supabase_key")
    )

def create_question_repository():
    """Create question repository"""
    return QuestionRepository(create_supabase_client())

def create_category_repository():
    """Create category repository"""
    return CategoryRepository(create_supabase_client())

def create_user_repository():
    """Create user repository"""
    return UserRepository(create_supabase_client())

def create_upload_repository():
    """Create upload repository"""
    return UploadRepository(create_supabase_client())

def create_question_generator():
    """Create question generator using the default provider from environment"""
    config = LLMConfigFactory.create_default()
    return QuestionGenerator(config)

def create_answer_generator():
    """Create answer generator using the default provider from environment"""
    config = LLMConfigFactory.create_default()
    return AnswerGenerator(config)

def create_deduplicator():
    """Create deduplicator - this still uses OpenAI for embeddings"""
    return Deduplicator()

def create_category_utils():
    """Create category utilities"""
    return CategoryUtils(create_category_repository())

# Factory methods for service creation
def create_question_service():
    """Create question service (original or refactored)"""
    question_repo = create_question_repository()
    category_repo = create_category_repository()
    generator = create_question_generator()
    answer_generator = create_answer_generator()
    deduplicator = create_deduplicator()
    
    if USE_REFACTORED_SERVICES:
        logger.info("Using refactored question service")
        return RefactoredQuestionService(
            question_repository=question_repo,
            question_generator=generator,
            answer_generator=answer_generator,
            deduplicator=deduplicator,
            category_repository=category_repo
        )
    else:
        logger.info("Using original question service")
        return QuestionService(
            question_repository=question_repo,
            question_generator=generator,
            answer_generator=answer_generator,
            deduplicator=deduplicator,
            category_repository=category_repo
        )

def create_upload_service():
    """Create upload service (original or refactored)"""
    supabase_client = create_supabase_client()
    upload_repo = create_upload_repository()
    category_repo = create_category_repository()
    
    if USE_REFACTORED_SERVICES:
        logger.info("Using refactored upload service")
        return RefactoredUploadService(upload_repo, category_repo)
    else:
        logger.info("Using original upload service")
        return UploadService(supabase_client, category_repo)

def create_user_service():
    """Create user service (original or refactored)"""
    supabase_client = create_supabase_client()
    user_repo = create_user_repository()
    
    if USE_REFACTORED_SERVICES:
        logger.info("Using refactored user service")
        return RefactoredUserService(user_repo)
    else:
        logger.info("Using original user service")
        return UserService(supabase_client)

def create_category_service():
    """Create category service (original or refactored)"""
    category_repo = create_category_repository()
    
    if USE_REFACTORED_SERVICES:
        logger.info("Using refactored category service")
        return RefactoredCategoryService(category_repo)
    else:
        logger.info("Using original category service")
        return CategoryService(category_repo)

# Create instances of all services using factory methods
category_service = create_category_service()
user_service = create_user_service()
upload_service = create_upload_service()
question_service = create_question_service()

# Create controller instances with appropriate services
category_controller = CategoryController(category_service)
auth_controller = AuthController(user_service)
upload_controller = UploadController(upload_service)
question_controller = QuestionController(question_service)

# Include routers
app.include_router(auth_controller.router)
app.include_router(upload_controller.router)
app.include_router(question_controller.router)
app.include_router(category_controller.router)

# Add more detailed documentation for the multi-difficulty endpoint
@app.post(
    "/questions/generate-multi-difficulty",
    response_model=List[MultiDifficultyResponse],
    tags=["questions"],
    summary="Generate questions with multiple difficulties concurrently",
    description="""
    Generate trivia questions with different difficulty levels concurrently.
    
    This endpoint allows you to specify how many questions to generate for each difficulty level,
    and processes all requests concurrently for faster generation.
    
    The response is grouped by difficulty level, making it easy to organize questions
    for games with progressive difficulty.
    
    Example request:
    ```json
    {
      "category": "Science",
      "difficulty_counts": {
        "Easy": 5,
        "Medium": 8,
        "Hard": 3
      },
      "deduplicate": true
    }
    ```
    """
)
async def generate_multi_difficulty_questions_proxy(request: MultiDifficultyRequest):
    """Proxy to controller method"""
    return await question_controller.generate_multi_difficulty_questions(request)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the Trivia App API"}

# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("Application startup")
    logger.info(f"Using {'refactored' if USE_REFACTORED_SERVICES else 'original'} services")

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)