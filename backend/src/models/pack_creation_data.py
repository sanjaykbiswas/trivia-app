# backend/src/models/pack_creation_data.py
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class PackCreationData(BaseModel):
    """
    Model representing metadata about pack creation.

    Attributes:
        id: Unique identifier for this metadata
        pack_id: Reference to the Pack this metadata belongs to. <--- ADDED
        is_pow: Whether this is a "proof of work" pack
        pow_analysis: Optional analysis of the proof of work
        creation_description: Optional description of the creation process
        pack_breadth: Description of the breadth of topics in the pack
        custom_difficulty_description: List of custom difficulty descriptions
        created_at: When this record was created
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    pack_id: uuid.UUID
    is_pow: Optional[bool] = False
    pow_analysis: Optional[str] = None
    creation_description: Optional[str] = None
    pack_breadth: str
    custom_difficulty_description: List[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        orm_mode = True