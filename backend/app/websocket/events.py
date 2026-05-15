from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID
from shared.types import WSEventType


@dataclass
class WSEvent:
    type: WSEventType
    payload: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "type": self.type.value if isinstance(self.type, WSEventType) else self.type,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }
