from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from services.upload_service import UploadService

# Pydantic models for API requests/responses
class QuestionUploadRequest(BaseModel):
    content: str
    category: str
    correct_answer: str
    incorrect_answers: List[str]
    difficulty: Optional[str] = None
    modified_difficulty: Optional[str] = None

class BulkUploadRequest(BaseModel):
    questions: List[QuestionUploadRequest]

class UserRegisterRequest(BaseModel):
    user_id: str
    username: Optional[str] = None

class CompleteQuestionResponse(BaseModel):
    id: str
    content: str
    category: str
    correct_answer: str
    incorrect_answers: List[str]
    difficulty: Optional[str] = None
    modified_difficulty: Optional[str] = None

class UploadController:
    """
    Controller for database upload API endpoints
    """
    def __init__(self, upload_service: UploadService):
        """
        Initialize with the upload service
        
        Args:
            upload_service (UploadService): Service for handling uploads
        """
        self.upload_service = upload_service
        self.router = APIRouter(prefix="/upload", tags=["upload"])
        self._setup_routes()
    
    def _setup_routes(self):
        """Set up API routes"""
        # IMPORTANT: Use method references, not lambdas which can cause issues
        self.router.post("/question", response_model=CompleteQuestionResponse)(self.upload_question)
        self.router.post("/questions/bulk", response_model=List[CompleteQuestionResponse])(self.bulk_upload_questions)
        self.router.post("/user", response_model=Dict[str, Any])(self.register_user)
    
    async def upload_question(self, request: QuestionUploadRequest) -> CompleteQuestionResponse:
        """
        Upload a single question with answer
        
        Args:
            request (QuestionUploadRequest): Question data
            
        Returns:
            CompleteQuestionResponse: Uploaded question data
        """
        try:
            result = await self.upload_service.upload_complete_question(
                question_content=request.content,
                category=request.category,
                correct_answer=request.correct_answer,
                incorrect_answers=request.incorrect_answers,
                difficulty=request.difficulty,
                modified_difficulty=request.modified_difficulty
            )
            
            return CompleteQuestionResponse(
                id=result.question.id,
                content=result.content,
                category=result.category,
                correct_answer=result.correct_answer,
                incorrect_answers=result.incorrect_answers,
                difficulty=result.difficulty,
                modified_difficulty=result.modified_difficulty
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    
    async def bulk_upload_questions(self, request: BulkUploadRequest) -> List[CompleteQuestionResponse]:
        """
        Upload multiple questions in bulk
        
        Args:
            request (BulkUploadRequest): Bulk question data
            
        Returns:
            List[CompleteQuestionResponse]: Uploaded questions data
        """
        try:
            # Convert request to list of dictionaries
            question_data = [q.dict() for q in request.questions]
            
            results = await self.upload_service.bulk_upload_complete_questions(question_data)
            
            return [
                CompleteQuestionResponse(
                    id=result.question.id,
                    content=result.content,
                    category=result.category,
                    correct_answer=result.correct_answer,
                    incorrect_answers=result.incorrect_answers,
                    difficulty=result.difficulty,
                    modified_difficulty=result.modified_difficulty
                ) for result in results
            ]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Bulk upload failed: {str(e)}")
    
    async def register_user(self, request: UserRegisterRequest) -> Dict[str, Any]:
        """
        Register a new user or ensure existing user
        
        Args:
            request (UserRegisterRequest): User data
            
        Returns:
            Dict[str, Any]: User data
        """
        try:
            return await self.upload_service.register_user(
                user_id=request.user_id,
                username=request.username
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"User registration failed: {str(e)}")