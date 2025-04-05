# backend/src/main.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware # Ensure this is imported
import logging
from contextlib import asynccontextmanager
from typing import Dict

from .api.routes import router as api_router
from .config.supabase_client import init_supabase_client, close_supabase_client
from .websocket_manager import ConnectionManager
from .utils import ensure_uuid
from .api.dependencies import get_game_service
from .services.game_service import GameService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

connection_manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan manager for FastAPI application.
    Initializes and closes resources when the application starts and shuts down.
    """
    # Initialize the Supabase client on startup
    logger.info("Initializing Supabase client...")
    supabase = await init_supabase_client()
    app.state.supabase = supabase

    # Make the manager instance available via app state
    app.state.connection_manager = connection_manager

    logger.info("Application startup complete")
    yield

    # Close the Supabase client on shutdown
    logger.info("Closing Supabase client...")
    await close_supabase_client(app.state.supabase)
    logger.info("Application shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="Trivia API",
    description="API for trivia pack and question generation",
    version="1.0.0",
    lifespan=lifespan,
)

# --- START CORRECTED CORS CONFIGURATION ---
# Define allowed origins
allowed_origins = [
    "https://trivia-im0a7qfa5-sanjay-personal-projects.vercel.app", # Your Vercel deployment
    "https://trivia-app-five-chi.vercel.app",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins, # Use the specific list
    allow_credentials=True,        # Keep this if you need credentials (cookies, auth headers)
    allow_methods=["*"],           # Allow all standard methods (GET, POST, PUT, DELETE, OPTIONS, etc.)
    allow_headers=["*"],           # Allow all standard headers
)
# --- END CORRECTED CORS CONFIGURATION ---

# Include API routes
app.include_router(api_router, prefix="/api")

# WebSocket Endpoint
@app.websocket("/ws/{game_id}/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    game_id: str,
    user_id: str,
    game_service: GameService = Depends(get_game_service)
):
    """WebSocket endpoint for real-time game communication."""
    try:
        # Basic validation (more robust validation might be needed depending on auth)
        game_id_uuid = ensure_uuid(game_id)
        user_id_uuid = ensure_uuid(user_id)
    except ValueError:
         logger.warning(f"WebSocket connection rejected: Invalid UUID format for game '{game_id}' or user '{user_id}'.")
         await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
         return

    # Use the global connection manager instance from app state
    manager = app.state.connection_manager
    await manager.connect(websocket, game_id_uuid, user_id_uuid)

    try:
        while True:
            # Keep connection open, listen for messages (optional)
            # If client sends messages, handle them here
            data = await websocket.receive_text()
            logger.debug(f"Received WebSocket message from {user_id_uuid} in {game_id_uuid}: {data}")
            # Example: Echo message back or handle specific commands
            # await manager.send_personal_message(f"You wrote: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, game_id_uuid, user_id_uuid)
        # Call the service to handle disconnect logic (like broadcasting user_left)
        try:
            await game_service.handle_disconnect(game_id_uuid, user_id_uuid)
        except Exception as service_error:
            logger.error(f"Error during GameService disconnect handling for User {user_id_uuid} in Game {game_id_uuid}: {service_error}", exc_info=True)
        logger.info(f"WebSocket disconnected cleanly for User {user_id_uuid} in Game {game_id_uuid}.")
    except Exception as e:
        # Log unexpected errors during WebSocket communication
        logger.error(f"WebSocket error for User {user_id_uuid} in Game {game_id_uuid}: {e}", exc_info=True)
        # Attempt to disconnect cleanly if possible
        manager.disconnect(websocket, game_id_uuid, user_id_uuid)
        # Consider calling handle_disconnect here too
        try:
            await game_service.handle_disconnect(game_id_uuid, user_id_uuid)
        except Exception as service_error:
            logger.error(f"Error during GameService disconnect handling (on WebSocket error) for User {user_id_uuid} in Game {game_id_uuid}: {service_error}", exc_info=True)

@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {"status": "ok", "message": "Trivia API is running"}

# Removed uvicorn runner - use run_api_server.py instead