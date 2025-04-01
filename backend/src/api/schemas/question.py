# backend/src/api/schemas/question.py
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

# Make sure the path to DifficultyLevel is correct for your structure
from ...models.question import DifficultyLevel

# --- NEW Schema for Difficulty Configuration ---
class DifficultyConfig(BaseModel):
    """Configuration for generating questions for a specific difficulty level."""
    difficulty: DifficultyLevel = Field(..., description="The specific difficulty level for this batch")
    num_questions: int = Field(5, description="Number of questions for this difficulty", ge=1, le=75)

# --- MODIFIED Schema for Topic Configuration ---
class TopicQuestionConfig(BaseModel):
    """Configuration for generating questions for a single topic across multiple difficulties."""
    topic: str = Field(..., description="The topic name")
    # Changed from single difficulty/num_questions to a list of configurations
    difficulty_configs: List[DifficultyConfig] = Field(..., description="List of difficulty configurations for this topic")
    custom_instructions: Optional[str] = Field(None, description="Optional custom instructions override for this specific topic")

# --- Batch Generation Request (uses updated TopicQuestionConfig) ---
class BatchQuestionGenerateRequest(BaseModel):
    """Request schema for batch question generation across multiple topics and difficulties."""
    topic_configs: List[TopicQuestionConfig] = Field(..., description="List of topic configurations, each specifying difficulties and counts")
    debug_mode: bool = Field(False, description="Enable verbose debug output globally for this batch")
    # Example: global_custom_instructions: Optional[str] = Field(None, description="Global custom instructions for all topics")

# --- Batch Generation Response (can be enhanced later) ---
class BatchQuestionGenerateResponse(BaseModel):
    """Response schema for batch question generation."""
    pack_id: str
    topics_processed: List[str] # Topics with at least one successful generation
    total_questions_generated: int
    status: str # e.g., "completed", "partial_failure", "failed"
    errors: Optional[List[str]] = None # List of topic names where at least one difficulty failed

# --- Other Schemas (remain largely the same) ---

class QuestionGenerateRequest(BaseModel):
    """Request schema for generating questions for a single topic/difficulty."""
    pack_topic: str = Field(..., description="Topic to generate questions for")
    difficulty: DifficultyLevel = Field(DifficultyLevel.MIXED, description="Difficulty level for the questions")
    num_questions: int = Field(5, description="Number of questions to generate", ge=1, le=75)
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
        use_enum_values = True # Ensure enums serialize to values in response

class QuestionsResponse(BaseModel):
    """Response schema for a list of questions."""
    total: int
    questions: List[QuestionResponse]

class SeedQuestionsResponse(BaseModel):
    """Response schema for seed questions."""
    count: int
    seed_questions: Dict[str, str]

# Schemas for custom instructions
class CustomInstructionsGenerateRequest(BaseModel):
    """Request schema for generating custom instructions."""
    pack_topic: str = Field(..., description="Topic to base custom instructions on")

class CustomInstructionsInputRequest(BaseModel):
    """Request schema for manually inputting custom instructions."""
    instructions: str = Field(..., description="Manually provided custom instructions")

class CustomInstructionsResponse(BaseModel):
    """Response schema for custom instructions."""
    custom_instructions: Optional[str] = Field(None, description="Custom instructions for question generation")