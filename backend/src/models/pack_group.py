# backend/src/models/pack_group.py
import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class PackGroup(BaseModel):
    """
    Model representing a group of question packs.
    
    Attributes:
        id: Unique identifier for the pack group
        name: Name of the pack group
        created_at: When this pack group was created
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        orm_mode = True