# backend/src/repositories/topic_repository.py
import uuid
from typing import List, Optional
from supabase import AsyncClient

from ..models.topic import Topic, TopicCreate, TopicUpdate
from .base_repository_impl import BaseRepositoryImpl
from ..utils import ensure_uuid

class TopicRepository(BaseRepositoryImpl[Topic, TopicCreate, TopicUpdate, str]):
    def __init__(self, db: AsyncClient):
        super().__init__(model=Topic, db=db, table_name="topics")

    async def get_by_pack_id(self, pack_id: str) -> List[Topic]:
        pack_id_str = ensure_uuid(pack_id)
        query = self.db.table(self.table_name).select("*").eq("pack_id", pack_id_str)
        response = await self._execute_query(query)
        return [self.model.model_validate(item) for item in response.data]

    async def get_by_name_and_pack_id(self, name: str, pack_id: str) -> Optional[Topic]:
        pack_id_str = ensure_uuid(pack_id)
        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("pack_id", pack_id_str)
            .eq("name", name)
            .limit(1)
        )
        response = await self._execute_query(query)
        if response.data:
            return self.model.model_validate(response.data[0])
        return None

    async def update_custom_instruction(self, topic_id: str, instruction: Optional[str]) -> Optional[Topic]:
        topic_id_str = ensure_uuid(topic_id)
        update_data = TopicUpdate(custom_instruction=instruction)
        return await self.update(id=topic_id_str, obj_in=update_data)

    async def create_topic(self, topic_create: TopicCreate) -> Optional[Topic]:
        # Optionally check for duplicates before creating if UNIQUE constraint isn't enough
        existing = await self.get_by_name_and_pack_id(topic_create.name, topic_create.pack_id)
        if existing:
            # Decide how to handle: return existing, raise error, or update?
            # For now, let's return existing to prevent duplicates
            return existing
        return await self.create(obj_in=topic_create)