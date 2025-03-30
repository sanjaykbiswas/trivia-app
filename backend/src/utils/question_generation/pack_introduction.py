# backend/src/utils/question_generation/pack_introduction.py
import uuid
from typing import Optional, Tuple
from ...repositories.pack_repository import PackRepository
from ..document_processing.processors import normalize_text

class PackIntroduction:
    """
    Handles the initial validation and setup for trivia pack creation.
    """
    
    def __init__(self, pack_repository: PackRepository):
        """
        Initialize with required repositories.
        
        Args:
            pack_repository: Repository for pack operations
        """
        self.pack_repository = pack_repository
        
    async def validate_creation_name(self, creation_name: str) -> Tuple[bool, Optional[uuid.UUID]]:
        """
        Check if a pack with the given creation name already exists.
        
        Args:
            creation_name: The name to validate (will be converted to lowercase)
            
        Returns:
            Tuple containing:
                - Boolean indicating if the pack exists
                - UUID of the existing pack (if found, otherwise None)
        """
        # Convert to lowercase as specified in requirements
        # Use normalize_text from document_processing.processors
        normalized_name = normalize_text(creation_name, lowercase=True)
        
        try:
            # Use the search_by_name method from the repository
            packs = await self.pack_repository.search_by_name(normalized_name)
            
            # Check for exact matches (case-insensitive)
            for pack in packs:
                if normalize_text(pack.name, lowercase=True) == normalized_name:
                    return True, pack.id
            
            # If we get here, no exact match was found
            return False, None
                
        except Exception as e:
            # Log the error (in a real application you'd use a proper logger)
            print(f"Error validating creation name: {str(e)}")
            # Re-raise for proper error handling upstream
            raise