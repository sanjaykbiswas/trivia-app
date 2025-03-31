# backend/src/api/schemas/question.py
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from ...models.question import DifficultyLevel

class QuestionGenerateRequest(BaseModel):
    """Request schema for generating questions."""
    pack_topic: str = Field(..., description="Topic to generate questions for")
    difficulty: DifficultyLevel = Field(..., description="Difficulty level for the questions")
    num_questions: int = Field(5, description="Number of questions to generate", ge=1, le=20)
    custom_instructions: Optional[str] = Field(None, description="Optional custom instructions for question generation")
    debug_mode: bool = Field(False, description="Enable verbose debug output")

class SeedQuestionRequest(BaseModel):
    """Request schema for storing seed questions."""
    seed_questions: Dict[str, str] = Field(..., description="Dictionary of question-answer pairs")

class SeedQuestionTextRequest(BaseModel):
    """Request schema for processing text to extract seed questions."""
    text_content: str = Field(..., description="Text content containing questions and answers")

class QuestionResponse(BaseModel):
    """Response schema for a question."""
    id: str
    question: str
    answer: str
    pack_id: str
    pack_topics_item: Optional[str] = None
    difficulty_initial: Optional[DifficultyLevel] = None
    difficulty_current: Optional[DifficultyLevel] = None
    correct_answer_rate: float
    created_at: datetime

    class Config:
        from_attributes = True

class QuestionsResponse(BaseModel):
    """Response schema for a list of questions."""
    total: int
    questions: List[QuestionResponse]

class SeedQuestionsResponse(BaseModel):
    """Response schema for seed questions."""
    count: int
    seed_questions: Dict[str, str]