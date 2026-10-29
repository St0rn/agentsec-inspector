from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any

from fastapi import WebSocket


class AuditEventHub:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, audit_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[audit_id].add(websocket)

    async def disconnect(self, audit_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections[audit_id].discard(websocket)

    async def publish(self, audit_id: str, event: dict[str, Any]) -> None:
        stale: list[WebSocket] = []
        for socket in list(self._connections.get(audit_id, set())):
            try:
                await socket.send_json(event)
            except Exception:
                stale.append(socket)
        if stale:
            async with self._lock:
                for socket in stale:
                    self._connections[audit_id].discard(socket)


event_hub = AuditEventHub()
