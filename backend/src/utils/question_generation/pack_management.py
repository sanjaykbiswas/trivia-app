# backend/src/utils/question_generation/pack_management.py
import uuid
from typing import Tuple, Optional
from ...models.pack import Pack, PackCreate, PackUpdate, CreatorType
from ...repositories.pack_repository import PackRepository
from ..question_generation.pack_introduction import PackIntroduction

async def get_or_create_pack(
    pack_repo: PackRepository,
    pack_name: str,
    pack_description: Optional[str] = None,
    price: float = 0.0,
    creator_type: CreatorType = CreatorType.SYSTEM,
    update_if_exists: bool = True
) -> Tuple[Pack, bool]:
    """
    Get an existing pack by name or create a new one if it doesn't exist.
    
    Args:
        pack_repo: PackRepository instance
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
    # Initialize PackIntroduction to check for existing packs
    pack_intro = PackIntroduction(pack_repository=pack_repo)
    
    # Check if a pack with this name already exists
    exists, existing_pack_id = await pack_intro.validate_creation_name(pack_name)
    
    if exists and existing_pack_id:
        # Pack exists, retrieve it
        existing_pack = await pack_repo.get_by_id(existing_pack_id)
        
        # Optionally update the description if provided and different
        if update_if_exists and pack_description and existing_pack.description != pack_description:
            update_data = PackUpdate(description=pack_description)
            existing_pack = await pack_repo.update(id=existing_pack_id, obj_in=update_data)
            
        return existing_pack, False
    
    # Pack doesn't exist, create a new one
    pack_data = PackCreate(
        name=pack_name,
        description=pack_description,
        price=price,
        creator_type=creator_type,
    )
    
    new_pack = await pack_repo.create(obj_in=pack_data)
    return new_pack, True