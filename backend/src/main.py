from fastapi import FastAPI, Depends
import supabase
from config.environment import Environment
from repositories.question_repository import QuestionRepository
from utils.question_generator.generator import QuestionGenerator
from utils.question_generator.answer_generator import AnswerGenerator
from utils.question_generator.deduplicator import Deduplicator
from services.question_service import QuestionService
from controllers.question_controller import QuestionController

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

def get_question_generator():
    """Create question generator"""
    return QuestionGenerator()

def get_answer_generator():
    """Create answer generator"""
    return AnswerGenerator()

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

# Include routers
app.include_router(question_controller.router)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the Trivia App API"}

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)