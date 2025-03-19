from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from services.question_service import QuestionService
from models.complete_question import CompleteQuestion

# Pydantic models for API requests/responses
class QuestionGenerationRequest(BaseModel):
    category: str
    count: int = Field(default=10, ge=1, le=100)
    deduplicate: bool = True
    difficulty: Optional[str] = None  # Changed from List[str] to single str
    user_id: Optional[str] = None

class MultiDifficultyRequest(BaseModel):
    category: str
    difficulty_counts: Dict[str, int] = Field(
        ..., 
        description="Map of difficulty levels to counts",
        example={"Easy": 5, "Medium": 8, "Hard": 3}
    )
    deduplicate: bool = True
    user_id: Optional[str] = None

class QuestionResponse(BaseModel):
    id: str
    content: str
    category: str
    difficulty: Optional[str] = None
    user_id: str = "00000000-0000-0000-0000-000000000000"  # System user UUID

class AnswerResponse(BaseModel):
    correct_answer: str
    incorrect_answers: List[str]

class CompleteQuestionResponse(BaseModel):
    id: str
    content: str
    category: str
    correct_answer: str
    incorrect_answers: List[str]
    difficulty: Optional[str] = None
    user_id: str = "00000000-0000-0000-0000-000000000000"  # System user UUID

class MultiDifficultyResponse(BaseModel):
    difficulty: str
    questions: List[CompleteQuestionResponse]

class QuestionController:
    """
    Controller for question-related API endpoints
    """
    def __init__(self, question_service: QuestionService):
        self.question_service = question_service
        self.router = APIRouter(prefix="/questions", tags=["questions"])
        self._setup_routes()
    
    def _setup_routes(self):
        """Set up API routes"""
        self.router.post("/generate", response_model=List[QuestionResponse])(self.generate_questions)
        self.router.post("/generate-complete", response_model=List[CompleteQuestionResponse])(self.generate_complete_questions)
        self.router.post("/generate-multi-difficulty", response_model=List[MultiDifficultyResponse])(self.generate_multi_difficulty_questions)
        self.router.get("/category/{category}", response_model=List[QuestionResponse])(self.get_by_category)
        self.router.get("/game", response_model=List[CompleteQuestionResponse])(self.get_game_questions)
        self.router.get("/{question_id}", response_model=CompleteQuestionResponse)(self.get_question)
    
    async def generate_questions(self, request: QuestionGenerationRequest) -> List[QuestionResponse]:
        """
        Generate new questions
        
        Args:
            request (QuestionGenerationRequest): Generation parameters
            
        Returns:
            List[QuestionResponse]: Generated questions
        """
        questions = await self.question_service.generate_and_save_questions(
            category=request.category,
            count=request.count,
            deduplicate=request.deduplicate,
            difficulty=request.difficulty,
            user_id=request.user_id
        )
        
        return [
            QuestionResponse(
                id=q.id,
                content=q.content,
                category=q.category,
                difficulty=q.difficulty,
                user_id=q.user_id
            ) for q in questions
        ]
    
    async def generate_complete_questions(self, request: QuestionGenerationRequest) -> List[CompleteQuestionResponse]:
        """
        Generate complete questions with answers
        
        Args:
            request (QuestionGenerationRequest): Generation parameters
            
        Returns:
            List[CompleteQuestionResponse]: Complete questions
        """
        complete_questions = await self.question_service.create_complete_question_set(
            category=request.category,
            count=request.count,
            deduplicate=request.deduplicate,
            difficulty=request.difficulty,
            user_id=request.user_id
        )
        
        return [self._format_complete_question(q) for q in complete_questions]
    
    async def generate_multi_difficulty_questions(self, request: MultiDifficultyRequest) -> List[MultiDifficultyResponse]:
        """
        Generate questions with multiple difficulties
        
        Args:
            request (MultiDifficultyRequest): Generation parameters with difficulty counts
            
        Returns:
            List[MultiDifficultyResponse]: Questions grouped by difficulty
        """
        try:
            result = await self.question_service.create_multi_difficulty_question_set(
                category=request.category,
                difficulty_counts=request.difficulty_counts,
                deduplicate=request.deduplicate,
                user_id=request.user_id
            )
            
            # Format the response
            response = []
            for difficulty, questions in result.items():
                response.append(
                    MultiDifficultyResponse(
                        difficulty=difficulty,
                        questions=[
                            CompleteQuestionResponse(
                                id=q.question.id,
                                content=q.content,
                                category=q.category,
                                correct_answer=q.correct_answer,
                                incorrect_answers=q.incorrect_answers,
                                difficulty=q.difficulty,
                                user_id=q.user_id
                            ) for q in questions
                        ]
                    )
                )
            
            return response
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Multi-difficulty generation failed: {str(e)}")
    
    async def get_by_category(self, category: str, limit: int = 50) -> List[QuestionResponse]:
        """
        Get questions by category
        
        Args:
            category (str): Category
            limit (int): Maximum results
            
        Returns:
            List[QuestionResponse]: Matching questions
        """
        questions = await self.question_service.get_questions_by_category(category, limit)
        
        return [
            QuestionResponse(
                id=q.id,
                content=q.content,
                category=q.category,
                difficulty=q.difficulty
            ) for q in questions
        ]
    
    async def get_game_questions(self, categories: Optional[List[str]] = None, count: int = 10) -> List[CompleteQuestionResponse]:
        """
        Get random questions for a game
        
        Args:
            categories (List[str], optional): Categories to include
            count (int): Number of questions
            
        Returns:
            List[CompleteQuestionResponse]: Random questions
        """
        questions = await self.question_service.get_random_game_questions(categories, count)
        
        return [self._format_complete_question(q) for q in questions]
    
    async def get_question(self, question_id: str) -> CompleteQuestionResponse:
        """
        Get a single question with answer
        
        Args:
            question_id (str): Question ID
            
        Returns:
            CompleteQuestionResponse: Complete question
        """
        question = await self.question_service.get_complete_question(question_id)
        
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        return self._format_complete_question(question)
    
    def _format_complete_question(self, question: CompleteQuestion) -> CompleteQuestionResponse:
        """
        Format a CompleteQuestion as API response
        
        Args:
            question (CompleteQuestion): Question to format
            
        Returns:
            CompleteQuestionResponse: Formatted response
        """
        return CompleteQuestionResponse(
            id=question.question.id,
            content=question.content,
            category=question.category,
            correct_answer=question.correct_answer,
            incorrect_answers=question.incorrect_answers,
            difficulty=question.difficulty,
            user_id=question.user_id
        )