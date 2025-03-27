from fastapi import FastAPI, Depends, Request
import supabase
import logging
import time
from utils.logging_config import setup_logging
from config.environment import Environment
from config.llm_config import LLMConfigFactory
from repositories.question_repository import QuestionRepository
from repositories.category_repository import CategoryRepository
from utils.question_generator.generator import QuestionGenerator
from utils.question_generator.answer_generator import AnswerGenerator
from utils.question_generator.deduplicator import Deduplicator
from utils.supabase_actions import SupabaseActions
from services.question_service import QuestionService
from services.upload_service import UploadService
from services.user_service import UserService
from services.category_service import CategoryService
from controllers.auth_controller import AuthController
from controllers.question_controller import QuestionController, MultiDifficultyRequest, MultiDifficultyResponse
from controllers.upload_controller import UploadController
from controllers.category_controller import CategoryController, CategoryResponse
from typing import List

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

# Create actual service instances
supabase_client = create_supabase_client()
question_repository = create_question_repository()
category_repository = create_category_repository()
question_generator = create_question_generator()
answer_generator = create_answer_generator()
deduplicator = create_deduplicator()

# Create the service instances
upload_service = UploadService(supabase_client)
user_service = UserService(supabase_client)
question_service = QuestionService(
    question_repository=question_repository,
    question_generator=question_generator,
    answer_generator=answer_generator,
    deduplicator=deduplicator
)
category_service = CategoryService(category_repository)

# Create controller instances
upload_controller = UploadController(upload_service)
question_controller = QuestionController(question_service)
auth_controller = AuthController(user_service)
category_controller = CategoryController(category_service)

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

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)