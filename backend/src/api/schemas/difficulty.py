# backend/src/api/schemas/difficulty.py
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class DifficultyDescription(BaseModel):
    """Schema for a single difficulty description."""
    base: str = Field(..., description="Base description for this difficulty level")
    custom: str = Field(..., description="Custom description for this difficulty level")

class DifficultyGenerateRequest(BaseModel):
    """Request schema for generating difficulty descriptions."""
    creation_name: Optional[str] = Field(None, description="Optional pack name to use for generation (defaults to pack's name)")
    force_regenerate: bool = Field(False, description="Whether to regenerate descriptions even if they already exist")

class DifficultyUpdateRequest(BaseModel):
    """Request schema for updating specific difficulty descriptions."""
    custom_descriptions: Dict[str, str] = Field(..., description="Mapping of difficulty levels to their custom descriptions")
    creation_name: Optional[str] = Field(None, description="Optional pack name to use for generation (defaults to pack's name)")

class DifficultyResponse(BaseModel):
    """Response schema for difficulty descriptions."""
    descriptions: Dict[str, DifficultyDescription] = Field(..., description="Mapping of difficulty levels to their descriptions")