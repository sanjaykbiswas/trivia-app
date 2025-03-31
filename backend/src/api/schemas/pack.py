# backend/src/api/schemas/pack.py
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

from ...models.pack import CreatorType

class PackCreateRequest(BaseModel):
    """Request schema for creating a new pack."""
    name: str = Field(..., description="Name of the pack")
    description: Optional[str] = Field(None, description="Optional description of the pack")
    price: float = Field(0.0, description="Price of the pack (default: 0.0 for free packs)")
    creator_type: CreatorType = Field(CreatorType.SYSTEM, description="Type of creator")
    pack_group_id: Optional[List[str]] = Field(None, description="Optional list of pack group IDs")

class PackResponse(BaseModel):
    """Response schema for pack data."""
    id: str
    name: str
    description: Optional[str] = None
    price: float
    pack_group_id: Optional[List[str]] = None
    creator_type: CreatorType
    correct_answer_rate: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True

class PackListResponse(BaseModel):
    """Response schema for list of packs."""
    total: int
    packs: List[PackResponse]