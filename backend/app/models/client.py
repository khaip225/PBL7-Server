import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Enum, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base
from shared.types import TaskType, ClientStatus


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    client_host: Mapped[str] = mapped_column(String(256), nullable=False)
    task_type: Mapped[TaskType | None] = mapped_column(Enum(TaskType, name="task_type"), nullable=True)
    status: Mapped[ClientStatus] = mapped_column(Enum(ClientStatus, name="client_status"), default=ClientStatus.OFFLINE, nullable=False)
    last_heartbeat: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    hardware_info: Mapped[dict] = mapped_column(JSONB, default=dict)
    dataset_info: Mapped[dict] = mapped_column(JSONB, default=dict)
    fl_client_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
