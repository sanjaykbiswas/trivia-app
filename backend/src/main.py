from fastapi import FastAPI, Depends
import supabase
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

# Create FastAPI app
app = FastAPI(
    title="Trivia App API",
    description="API for managing trivia questions and games",
    version="1.0.0"
)

# Dependency injection setup

def get_environment():
    """Get environment singleton"""
    return Environment()

def get_supabase_client(env: Environment = Depends(get_environment)):
    """Create Supabase client"""
    return supabase.create_client(
        supabase_url=env.get("supabase_url"),
        supabase_key=env.get("supabase_key")
    )

def get_question_repository(client = Depends(get_supabase_client)):
    """Create question repository"""
    return QuestionRepository(client)

def get_upload_service(client = Depends(get_supabase_client)):
    """Create upload service"""
    return UploadService(client)

def get_question_generator():
    """Create question generator with Claude for rich, creative questions"""
    config = LLMConfigFactory.create_anthropic("claude-3-7-sonnet-20250219")
    return QuestionGenerator(config)

def get_answer_generator():
    """Create answer generator with GPT for fast, structured answers"""
    config = LLMConfigFactory.create_openai("gpt-3.5-turbo")
    return AnswerGenerator(config)

def get_deduplicator():
    """Create deduplicator"""
    return Deduplicator()

def get_question_service(
    repository: QuestionRepository = Depends(get_question_repository),
    generator: QuestionGenerator = Depends(get_question_generator),
    answer_generator: AnswerGenerator = Depends(get_answer_generator),
    deduplicator: Deduplicator = Depends(get_deduplicator)
):
    """Create question service"""
    return QuestionService(
        question_repository=repository,
        question_generator=generator,
        answer_generator=answer_generator,
        deduplicator=deduplicator
    )

# Initialize controllers
question_controller = QuestionController(Depends(get_question_service))
upload_controller = UploadController(Depends(get_upload_service))

# Include routers
app.include_router(question_controller.router)
app.include_router(upload_controller.router)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the Trivia App API"}

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)