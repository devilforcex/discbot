"""WebSocket manager for real-time player state broadcasting."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections per guild and broadcasts state updates."""

    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, guild_id: int) -> None:
        await websocket.accept()
        if guild_id not in self._connections:
            self._connections[guild_id] = set()
        self._connections[guild_id].add(websocket)
        logger.info("WS connected: guild=%s (total=%d)", guild_id, len(self._connections[guild_id]))

    def disconnect(self, websocket: WebSocket, guild_id: int) -> None:
        if guild_id in self._connections:
            self._connections[guild_id].discard(websocket)
            if not self._connections[guild_id]:
                del self._connections[guild_id]
        logger.info("WS disconnected: guild=%s", guild_id)

    async def broadcast(self, guild_id: int, event: str, data: dict[str, Any]) -> None:
        if guild_id not in self._connections:
            return
        payload = json.dumps({"event": event, "data": data})
        dead: list[WebSocket] = []
        for ws in self._connections[guild_id]:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._connections[guild_id].discard(ws)
        if not self._connections.get(guild_id):
            self._connections.pop(guild_id, None)

    def get_connected_guilds(self) -> list[int]:
        return list(self._connections.keys())


ws_manager = ConnectionManager()
