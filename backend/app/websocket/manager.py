import uuid
from fastapi import WebSocket
from .events import WSEvent
from shared.types import WSEventType


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, WebSocket] = {}
        self._subscriptions: dict[str, set[str]] = {}

    async def connect(self, ws: WebSocket) -> str:
        await ws.accept()
        session_id = str(uuid.uuid4())
        self._connections[session_id] = ws
        self._subscriptions[session_id] = set()
        await ws.send_json(WSEvent(type=WSEventType.CONNECTED, payload={"session_id": session_id}).to_dict())
        return session_id

    async def disconnect(self, session_id: str):
        self._connections.pop(session_id, None)
        self._subscriptions.pop(session_id, None)

    async def subscribe(self, session_id: str, job_id: str | None):
        if session_id in self._subscriptions:
            if job_id:
                self._subscriptions[session_id].add(job_id)
            else:
                self._subscriptions[session_id].clear()

    async def unsubscribe(self, session_id: str, job_id: str):
        if session_id in self._subscriptions:
            self._subscriptions[session_id].discard(job_id)

    async def broadcast(self, event: WSEvent):
        dead = []
        for sid, ws in self._connections.items():
            try:
                await ws.send_json(event.to_dict())
            except Exception:
                dead.append(sid)
        for sid in dead:
            await self.disconnect(sid)

    async def send_to_job(self, job_id: str, event: WSEvent):
        dead = []
        for sid, ws in self._connections.items():
            subs = self._subscriptions.get(sid, set())
            # Empty subscriptions = receive all events
            if not subs or job_id in subs:
                try:
                    await ws.send_json(event.to_dict())
                except Exception:
                    dead.append(sid)
        for sid in dead:
            await self.disconnect(sid)

    async def send_personal(self, session_id: str, event: WSEvent):
        ws = self._connections.get(session_id)
        if ws:
            try:
                await ws.send_json(event.to_dict())
            except Exception:
                await self.disconnect(session_id)

    @property
    def active_count(self) -> int:
        return len(self._connections)


ws_manager = ConnectionManager()
