import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base
from shared.types import TaskType, JobStatus, AggregationStrategy


class TrainingJob(Base):
    __tablename__ = "training_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    task_type: Mapped[TaskType] = mapped_column(Enum(TaskType, name="task_type"), nullable=False)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus, name="job_status"), default=JobStatus.DRAFT, nullable=False)
    strategy: Mapped[AggregationStrategy] = mapped_column(Enum(AggregationStrategy, name="aggregation_strategy"), default=AggregationStrategy.FEDAVG, nullable=False)
    strategy_params: Mapped[dict] = mapped_column(JSONB, default=dict)
    num_rounds: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    min_clients: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    min_samples: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    model_config: Mapped[dict] = mapped_column(JSONB, default=dict)
    flower_config: Mapped[dict] = mapped_column(JSONB, default=dict)
    pid: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_round: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    joined_clients: Mapped[dict] = mapped_column(JSONB, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    rounds = relationship("Round", back_populates="job", cascade="all, delete-orphan")
    checkpoints = relationship("Checkpoint", back_populates="job", cascade="all, delete-orphan")
