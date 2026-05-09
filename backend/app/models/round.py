import uuid
from datetime import datetime
from sqlalchemy import Integer, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class Round(Base):
    __tablename__ = "rounds"
    __table_args__ = (UniqueConstraint("job_id", "round_number"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("training_jobs.id", ondelete="CASCADE"), nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    num_clients: Mapped[int] = mapped_column(Integer, nullable=False)
    num_skipped: Mapped[int] = mapped_column(Integer, default=0)
    loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    client_metrics: Mapped[list] = mapped_column(JSONB, default=list)
    aggregated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    job = relationship("TrainingJob", back_populates="rounds")
