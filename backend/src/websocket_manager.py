# backend/src/websocket_manager.py
import asyncio
import json
import logging
from typing import Dict, List, Set, Optional
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages active WebSocket connections for game rooms."""

    def __init__(self):
        # Structure: {game_id: {user_id: WebSocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        logger.info("ConnectionManager initialized.")

    async def connect(self, websocket: WebSocket, game_id: str, user_id: str):
        """Accepts and stores a new WebSocket connection."""
        await websocket.accept()
        if game_id not in self.active_connections:
            self.active_connections[game_id] = {}
        self.active_connections[game_id][user_id] = websocket
        logger.info(f"WebSocket connected: User {user_id} in Game {game_id}. Total in game: {len(self.active_connections[game_id])}")
        # Optionally send a welcome message or current state upon connection
        # await self.send_personal_message({"type": "status", "message": "Connected"}, websocket)

    def disconnect(self, websocket: WebSocket, game_id: str, user_id: str):
        """Removes a WebSocket connection."""
        if game_id in self.active_connections:
            if user_id in self.active_connections[game_id]:
                # Ensure the websocket object matches before deleting, though user_id should be unique per game
                if self.active_connections[game_id][user_id] == websocket:
                    del self.active_connections[game_id][user_id]
                    logger.info(f"WebSocket disconnected: User {user_id} from Game {game_id}.")
                    if not self.active_connections[game_id]:
                        del self.active_connections[game_id]
                        logger.info(f"Game room {game_id} empty, removed.")
            else:
                 logger.warning(f"User {user_id} not found in game {game_id} during disconnect.")
        else:
             logger.warning(f"Game room {game_id} not found during disconnect for user {user_id}.")


    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Sends a JSON message to a specific WebSocket client."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            # Log error, connection might be closed unexpectedly
            logger.error(f"Failed to send personal message: {e}", exc_info=False) # Avoid full tb for send errors usually

    async def broadcast(self, message: dict, game_id: str):
        """Broadcasts a JSON message to all clients in a specific game room."""
        if game_id in self.active_connections:
            connections = list(self.active_connections[game_id].values()) # Create list to avoid issues if dict changes during iteration
            message_json = json.dumps(message) # Serialize once
            logger.debug(f"Broadcasting to {len(connections)} clients in game {game_id}: {message_json}")

            # Use asyncio.gather for concurrent sending
            results = await asyncio.gather(
                *[conn.send_text(message_json) for conn in connections],
                return_exceptions=True
            )

            # Log any exceptions that occurred during sending
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                     # Find the user_id associated with the failed connection if possible
                     failed_user_id = "unknown"
                     for uid, ws in self.active_connections.get(game_id, {}).items():
                         if ws == connections[i]:
                             failed_user_id = uid
                             break
                     logger.error(f"Failed to broadcast to user {failed_user_id} in game {game_id}: {result}", exc_info=False)
                     # Consider removing the problematic connection here if appropriate
                     # self.disconnect(connections[i], game_id, failed_user_id)
        else:
            logger.warning(f"Attempted to broadcast to non-existent game room: {game_id}")

    async def broadcast_to_others(self, message: dict, game_id: str, sender_user_id: str):
        """Broadcasts a JSON message to all clients in a room EXCEPT the sender."""
        if game_id in self.active_connections:
            message_json = json.dumps(message)
            tasks = []
            count = 0
            for user_id, websocket in self.active_connections[game_id].items():
                if user_id != sender_user_id:
                    tasks.append(websocket.send_text(message_json))
                    count += 1

            logger.debug(f"Broadcasting to {count} others in game {game_id} (excluding {sender_user_id}): {message_json}")
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Log any exceptions
            # (Error logging similar to broadcast can be added here if needed)


    def get_connected_user_ids(self, game_id: str) -> List[str]:
         """Returns a list of user IDs currently connected in a game room."""
         if game_id in self.active_connections:
             return list(self.active_connections[game_id].keys())
         return []