import json
import re
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.event_log import EventLog
from ..database import async_session
from ..websocket.manager import ws_manager
from ..websocket.events import WSEvent
from shared.types import WSEventType, EventSeverity

# Regex patterns for Flower server structured output
PATTERNS = [
    (re.compile(r"EVENT:job_started:(.+)$"), WSEventType.JOB_STARTED, EventSeverity.INFO),
    (re.compile(r"EVENT:server_ready:(.+)$"), WSEventType.JOB_STARTED, EventSeverity.INFO),
    (re.compile(r"EVENT:round_completed:(.+)$"), WSEventType.ROUND_COMPLETED, EventSeverity.INFO),
    (re.compile(r"EVENT:checkpoint_saved:(.+)$"), WSEventType.CHECKPOINT_SAVED, EventSeverity.INFO),
    (re.compile(r"EVENT:job_completed:(.+)$"), WSEventType.JOB_COMPLETED, EventSeverity.INFO),
]

# Additional natural language patterns
NL_PATTERNS = [
    (re.compile(r"\[(Audio|Image)\]\s+Round\s+(\d+):\s+Tong\s+hop\s+(\d+)\s+client"), WSEventType.AGGREGATION_COMPLETED),
    (re.compile(r"\[(Audio|Image)\]\s+Round\s+(\d+):\s+bo\s+(\d+)\s+client"), WSEventType.ROUND_STARTED),
    (re.compile(r"✅\s+Client\s+(\S+):\s+(\d+)\s+samples,\s+Loss:\s+([\d.]+)"), WSEventType.CLIENT_TRAINING_COMPLETED),
    (re.compile(r"💾\s+Da\s+luu\s+model:\s+(.+)"), WSEventType.CHECKPOINT_SAVED),
    (re.compile(r"Khoi\s+dong\s+FL\s+Server"), WSEventType.JOB_STARTED),
]


class FlowerLogParser:
    def __init__(self, job_id: uuid.UUID | None = None):
        self.job_id = str(job_id) if job_id else None

    async def feed_line(self, line: str):
        line = line.strip()
        if not line:
            return

        # Try structured EVENT: patterns first
        for pattern, event_type, severity in PATTERNS:
            m = pattern.search(line)
            if m:
                try:
                    payload = json.loads(m.group(1))
                except json.JSONDecodeError:
                    payload = {"raw": m.group(1)}
                await self._emit(event_type, payload, severity)
                return

        # Try natural language patterns
        for pattern, event_type in NL_PATTERNS:
            m = pattern.search(line)
            if m:
                groups = m.groups()
                payload = {"raw": line, "match": list(groups)}
                if event_type == WSEventType.AGGREGATION_COMPLETED:
                    payload["task_type"] = groups[0].lower() if len(groups) > 0 else None
                    payload["round"] = int(groups[1]) if len(groups) > 1 else None
                    payload["num_clients"] = int(groups[2]) if len(groups) > 2 else None
                elif event_type == WSEventType.CLIENT_TRAINING_COMPLETED:
                    payload["client_id"] = groups[0] if len(groups) > 0 else None
                    payload["num_samples"] = int(groups[1]) if len(groups) > 1 else None
                    payload["loss"] = float(groups[2]) if len(groups) > 2 else None
                elif event_type == WSEventType.CHECKPOINT_SAVED:
                    payload["file_path"] = groups[0] if len(groups) > 0 else None
                await self._emit(event_type, payload, EventSeverity.INFO)
                return

        # Fallback: treat as system event if contains keywords
        if any(kw in line.lower() for kw in ["error", "fail", "exception", "traceback"]):
            await self._emit(WSEventType.ERROR_EVENT, {"message": line}, EventSeverity.ERROR)
        else:
            await self._emit(WSEventType.SYSTEM_EVENT, {"message": line}, EventSeverity.INFO)

    async def _emit(self, event_type: WSEventType, payload: dict, severity: EventSeverity):
        payload["job_id"] = self.job_id

        # Persist to DB
        async with async_session() as db:
            event = EventLog(
                job_id=uuid.UUID(self.job_id) if self.job_id else None,
                event_type=event_type.value if isinstance(event_type, WSEventType) else event_type,
                severity=severity,
                payload=payload,
                created_at=datetime.now(timezone.utc),
            )
            db.add(event)
            await db.commit()

        # Broadcast via WebSocket
        ws_event = WSEvent(type=event_type, payload=payload)
        if self.job_id:
            await ws_manager.send_to_job(self.job_id, ws_event)
        else:
            await ws_manager.broadcast(ws_event)
