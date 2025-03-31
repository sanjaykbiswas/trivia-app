# backend/src/utils/__init__.py
"""
Utilities module for the Trivia application.

This package contains utility functions and classes for various
application needs, including LLM integration and question generation.
"""

import uuid
import re
from typing import Union

# Update ensure_uuid to validate and return string UUIDs
def ensure_uuid(id_value: Union[str, uuid.UUID, bytes]) -> str:
    """
    Ensures the given value is a valid UUID and returns its string representation.
    
    Args:
        id_value: A string, UUID object, or bytes representing a UUID
        
    Returns:
        A string representation of the UUID
        
    Raises:
        ValueError: If the input cannot be converted to a UUID
    """
    # If already a string, validate it's a valid UUID format
    if isinstance(id_value, str):
        # Simple validation using regex pattern for UUID format
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if re.match(uuid_pattern, id_value.lower()):
            return id_value
        # If not matching the pattern, try to create a UUID to validate and get string
        return str(uuid.UUID(id_value))
    
    # If it's a UUID object, convert to string
    if isinstance(id_value, uuid.UUID):
        return str(id_value)
    
    # Otherwise try to create a UUID from the value
    return str(uuid.UUID(id_value))