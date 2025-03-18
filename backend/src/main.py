from fastapi import FastAPI, Depends, Request
import supabase
import logging
import time
from utils.logging_config import setup_logging
from config.environment import Environment
from config.llm_config import LLMConfigFactory
from repositories.question_repository import QuestionRepository
from utils.question_generator.generator import QuestionGenerator
from utils.question_generator.answer_generator import AnswerGenerator
from utils.question_generator.deduplicator import Deduplicator
from utils.supabase_actions import SupabaseActions
from services.question_service import QuestionService
from services.upload_service import UploadService
from controllers.question_controller import QuestionController
from controllers.upload_controller import UploadController

# Set up logging
logger = setup_logging()

# Create FastAPI app
app = FastAPI(
    title="Trivia App API",
    description="API for managing trivia questions and games",
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

def create_question_generator():
    """Create question generator with Claude for rich, creative questions"""
    config = LLMConfigFactory.create_anthropic("claude-3-7-sonnet-20250219")
    return QuestionGenerator(config)

def create_answer_generator():
    """Create answer generator with GPT for fast, structured answers"""
    config = LLMConfigFactory.create_openai("gpt-4o")
    return AnswerGenerator(config)

def create_deduplicator():
    """Create deduplicator"""
    return Deduplicator()

# Create actual service instances
supabase_client = create_supabase_client()
question_repository = create_question_repository()
question_generator = create_question_generator()
answer_generator = create_answer_generator()
deduplicator = create_deduplicator()

# Create the service instances
upload_service = UploadService(supabase_client)
question_service = QuestionService(
    question_repository=question_repository,
    question_generator=question_generator,
    answer_generator=answer_generator,
    deduplicator=deduplicator
)

# Create controller instances with the actual services
upload_controller = UploadController(upload_service)
question_controller = QuestionController(question_service)

# Include router
app.include_router(upload_controller.router)
app.include_router(question_controller.router)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the Trivia App API"}

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)