# backend/src/repositories/pack_creation_data_repository.py
import uuid
from typing import Optional
from supabase_py_async import AsyncClient

from ..models.pack_creation_data import PackCreationData
from .base_repository_impl import BaseRepositoryImpl

class PackCreationDataRepository(BaseRepositoryImpl[PackCreationData, PackCreationData, PackCreationData, uuid.UUID]):
    """
    Repository for managing PackCreationData in Supabase.
    """
    def __init__(self, db: AsyncClient):
        super().__init__(model=PackCreationData, db=db, table_name="pack_creation_data") # Table name: "pack_creation_data"

    # --- Custom PackCreationData-specific methods (if any) ---
    # This model seems primarily metadata, might not need many custom queries.
    # Example: Find by pack_id if you add a pack_id foreign key to this table/model
    # async def get_by_pack_id(self, pack_id: uuid.UUID) -> Optional[PackCreationData]:
    #     query = self.db.table(self.table_name).select("*").eq("pack_id", str(pack_id)).limit(1)
    #     response = await self._execute_query(query)
    #     if response.data:
    #         return self.model.parse_obj(response.data[0])
    #     return None