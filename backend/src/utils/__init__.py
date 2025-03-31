# backend/src/utils/__init__.py
"""
Utilities module for the Trivia application.

This package contains utility functions and classes for various
application needs, including LLM integration and question generation.
"""

import uuid
from typing import Union

# Import specific utility modules if needed for direct import from utils

def ensure_uuid(id_value: Union[str, uuid.UUID, bytes]) -> uuid.UUID:
    """
    Ensures the given value is converted to a UUID object.
    
    Args:
        id_value: A string, UUID object, or bytes representing a UUID
        
    Returns:
        A UUID object
        
    Raises:
        ValueError: If the input cannot be converted to a UUID
    """
    if isinstance(id_value, uuid.UUID):
        return id_value
    return uuid.UUID(id_value)