# backend/src/repositories/pack_creation_data_repository.py
import uuid
from typing import Optional
from supabase import AsyncClient

from ..models.pack_creation_data import PackCreationData, PackCreationDataCreate, PackCreationDataUpdate
from .base_repository_impl import BaseRepositoryImpl
from ..utils import ensure_uuid

class PackCreationDataRepository(BaseRepositoryImpl[PackCreationData, PackCreationDataCreate, PackCreationDataUpdate, uuid.UUID]):
    """
    Repository for managing PackCreationData in Supabase.
    Contains metadata linked to a specific pack.
    """
    def __init__(self, db: AsyncClient):
        super().__init__(model=PackCreationData, db=db, table_name="pack_creation_data") # Table name: "pack_creation_data"

    # --- Custom PackCreationData-specific method ---

    async def get_by_pack_id(self, pack_id: uuid.UUID) -> Optional[PackCreationData]:
        """Retrieve pack creation metadata by the associated pack_id."""
        # Ensure pack_id is a proper UUID object
        pack_id = ensure_uuid(pack_id)
        
        # Assuming a one-to-one relationship between pack and its creation data
        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("pack_id", str(pack_id)) # Filter by pack_id
            .limit(1) # Expecting only one entry per pack
        )
        response = await self._execute_query(query)
        if response.data:
            return self.model.parse_obj(response.data[0])
        return None

    async def delete_by_pack_id(self, pack_id: uuid.UUID) -> Optional[PackCreationData]:
        """Deletes creation data associated with a specific pack_id."""
        # Ensure pack_id is a proper UUID object
        pack_id = ensure_uuid(pack_id)
        
        # First, get the data to return later
        data = await self.get_by_pack_id(pack_id)
        
        if data:
            # Then delete it
            query = (
                self.db.table(self.table_name)
                .delete()
                .eq("pack_id", str(pack_id))
            )
            await self._execute_query(query)
            
        return data