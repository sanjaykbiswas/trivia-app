# backend/src/services/pack_service.py
from typing import Tuple, Optional, List
import logging
import traceback

from ..models.pack import Pack, PackCreate, PackUpdate, CreatorType
from ..repositories.pack_repository import PackRepository
from ..utils import ensure_uuid

# Configure logger
logger = logging.getLogger(__name__)

class PackService:
    """
    Service for pack management operations.
    Handles business logic related to creating, retrieving, and validating packs.
    """
    
    def __init__(self, pack_repository: PackRepository):
        """
        Initialize the service with required repositories.
        
        Args:
            pack_repository: Repository for pack operations
        """
        self.pack_repository = pack_repository
    
    async def validate_creation_name(self, creation_name: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a pack with the given creation name already exists.
        
        Args:
            creation_name: The name to validate (will be converted to lowercase)
            
        Returns:
            Tuple containing:
                - Boolean indicating if the pack exists
                - ID of the existing pack (if found, otherwise None)
        """
        # Import here to avoid circular imports
        from ..utils.document_processing.processors import normalize_text
        
        try:
            # Convert to lowercase as specified in requirements
            normalized_name = normalize_text(creation_name, lowercase=True)
            
            # Use the search_by_name method from the repository
            packs = await self.pack_repository.search_by_name(normalized_name)
            
            # Check for exact matches (case-insensitive)
            for pack in packs:
                if normalize_text(pack.name, lowercase=True) == normalized_name:
                    return True, pack.id
            
            # If we get here, no exact match was found
            return False, None
                
        except Exception as e:
            # Log the error with full traceback
            logger.error(f"Error validating creation name: {str(e)}")
            logger.error(traceback.format_exc())
            # Re-raise for proper error handling upstream
            raise
    
    async def get_all_packs(self, skip: int = 0, limit: int = 100) -> List[Pack]:
        """
        Get all packs with pagination.
        
        Args:
            skip: Number of packs to skip (pagination offset)
            limit: Maximum number of packs to return
            
        Returns:
            List of Pack objects
        """
        try:
            return await self.pack_repository.get_all(skip=skip, limit=limit)
        except Exception as e:
            logger.error(f"Error retrieving all packs: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    async def get_or_create_pack(
        self,
        pack_name: str,
        pack_description: Optional[str] = None,
        price: float = 0.0,
        creator_type: CreatorType = CreatorType.SYSTEM,
        update_if_exists: bool = True
    ) -> Tuple[Pack, bool]:
        """
        Get an existing pack by name or create a new one if it doesn't exist.
        
        Args:
            pack_name: Name of the pack to get or create
            pack_description: Optional description for the pack
            price: Price of the pack (default: 0.0 for free packs)
            creator_type: Type of creator (default: SYSTEM)
            update_if_exists: Whether to update the description of an existing pack
            
        Returns:
            Tuple containing:
                - The existing or newly created Pack
                - Boolean indicating if the pack was newly created (True) or existed (False)
        """
        try:
            # Check if a pack with this name already exists
            exists, existing_pack_id = await self.validate_creation_name(pack_name)
            
            if exists and existing_pack_id:
                # Ensure existing_pack_id is a valid UUID string
                existing_pack_id_str = ensure_uuid(existing_pack_id)
                
                logger.info(f"Found existing pack with ID: {existing_pack_id_str}")
                
                # Pack exists, retrieve it
                existing_pack = await self.pack_repository.get_by_id(existing_pack_id_str)
                
                # Optionally update the description if provided and different
                if update_if_exists and pack_description and existing_pack.description != pack_description:
                    logger.info(f"Updating description for pack ID: {existing_pack_id_str}")
                    update_data = PackUpdate(description=pack_description)
                    existing_pack = await self.pack_repository.update(id=existing_pack_id_str, obj_in=update_data)
                    
                return existing_pack, False
            
            logger.info(f"Creating new pack: {pack_name}")
            # Pack doesn't exist, create a new one
            pack_data = PackCreate(
                name=pack_name,
                description=pack_description,
                price=price,
                creator_type=creator_type,
            )
            
            new_pack = await self.pack_repository.create(obj_in=pack_data)
            logger.info(f"Created new pack with ID: {new_pack.id}")
            return new_pack, True
        
        except Exception as e:
            logger.error(f"Error in get_or_create_pack: {str(e)}")
            logger.error(traceback.format_exc())
            raise