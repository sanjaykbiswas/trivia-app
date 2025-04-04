from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager
from typing import Dict

# --- MODIFIED IMPORTS ---
from .api.routes import router as api_router
from .config.supabase_client import init_supabase_client, close_supabase_client
from .websocket_manager import ConnectionManager # Import the manager
from .utils import ensure_uuid # Import ensure_uuid
# --- END MODIFIED IMPORTS ---

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# --- ADD Connection Manager Instance ---
# This instance will be shared across the application
connection_manager = ConnectionManager()
# --- END ADD ---


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

    # --- ADD Manager to App State ---
    # Make the manager instance available via app state for potential dependency injection
    app.state.connection_manager = connection_manager
    # --- END ADD ---

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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

# --- ADD WebSocket Endpoint ---
@app.websocket("/ws/{game_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str, user_id: str):
    """WebSocket endpoint for real-time game communication."""
    try:
        # Basic validation (more robust validation might be needed depending on auth)
        game_id_uuid = ensure_uuid(game_id)
        user_id_uuid = ensure_uuid(user_id)
    except ValueError:
         logger.warning(f"WebSocket connection rejected: Invalid UUID format for game '{game_id}' or user '{user_id}'.")
         await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
         return

    # Use the global connection manager instance
    manager = app.state.connection_manager
    await manager.connect(websocket, game_id_uuid, user_id_uuid)

    # Example: Notify others that a user joined (moved this logic to GameService.join_game)
    # await manager.broadcast(
    #     {"type": "user_joined", "user_id": user_id_uuid, "game_id": game_id_uuid},
    #     game_id_uuid
    # )

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
        # Example: Notify others that a user left (move this logic to where disconnects are handled, e.g., GameService)
        # await manager.broadcast(
        #     {"type": "user_left", "user_id": user_id_uuid, "game_id": game_id_uuid},
        #     game_id_uuid
        # )
        logger.info(f"WebSocket disconnected cleanly for User {user_id_uuid} in Game {game_id_uuid}.")
    except Exception as e:
        # Log unexpected errors during WebSocket communication
        logger.error(f"WebSocket error for User {user_id_uuid} in Game {game_id_uuid}: {e}", exc_info=True)
        # Attempt to disconnect cleanly if possible
        manager.disconnect(websocket, game_id_uuid, user_id_uuid)
        # Optionally broadcast an error or disconnect message

# --- END ADD WebSocket Endpoint ---


@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {"status": "ok", "message": "Trivia API is running"}

# Removed uvicorn runner - use run_api_server.py instead
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)