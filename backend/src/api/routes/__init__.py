# backend/src/api/routes/__init__.py
from fastapi import APIRouter

from .pack import router as pack_router
from .topic import router as topic_router
from .difficulty import router as difficulty_router
from .question import router as question_router
from .game import router as game_router  # Add this line

# Create main router
router = APIRouter()

# Include all route modules
router.include_router(pack_router, prefix="/packs", tags=["packs"])
router.include_router(topic_router, prefix="/packs/{pack_id}/topics", tags=["topics"])
router.include_router(difficulty_router, prefix="/packs/{pack_id}/difficulties", tags=["difficulties"])
router.include_router(question_router, prefix="/packs/{pack_id}/questions", tags=["questions"])
router.include_router(game_router, prefix="/games", tags=["games"])  # Add this line