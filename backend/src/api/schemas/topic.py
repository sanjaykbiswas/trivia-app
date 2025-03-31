# backend/src/api/schemas/topic.py
from typing import List, Optional
from pydantic import BaseModel, Field

class TopicGenerateRequest(BaseModel):
    """Request schema for generating topics."""
    num_topics: int = Field(5, description="Number of topics to generate", ge=1, le=20)
    creation_name: Optional[str] = Field(None, description="Optional pack name to use for generation (defaults to pack's name)")
    predefined_topic: Optional[str] = Field(None, description="Optional predefined topic to use instead of generating")

class TopicAddRequest(BaseModel):
    """Request schema for adding additional topics."""
    num_additional_topics: int = Field(3, description="Number of additional topics to generate", ge=1, le=10)
    creation_name: Optional[str] = Field(None, description="Optional pack name to use for generation (defaults to pack's name)")
    predefined_topic: Optional[str] = Field(None, description="Optional predefined topic to add directly")

class TopicResponse(BaseModel):
    """Response schema for topics."""
    topics: List[str] = Field(..., description="List of generated topics")