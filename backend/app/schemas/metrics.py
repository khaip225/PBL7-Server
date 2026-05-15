from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class ClientRoundMetric(BaseModel):
    client_id: str
    client_name: str
    num_samples: int
    loss: float
    accuracy: float | None = None


class RoundMetricsResponse(BaseModel):
    id: UUID
    round_number: int
    loss: float | None = None
    accuracy: float | None = None
    num_clients: int
    num_skipped: int
    duration_seconds: float | None = None
    client_metrics: list[ClientRoundMetric] = []
    aggregated_at: datetime

    model_config = {"from_attributes": True}


class ConvergenceData(BaseModel):
    job_id: UUID
    rounds: list[RoundMetricsResponse]
    best_loss: float | None = None
    best_accuracy: float | None = None
    best_round: int | None = None


class OverviewMetrics(BaseModel):
    total_clients: int
    online_clients: int
    active_jobs: int
    completed_jobs: int
    total_checkpoints: int
    best_accuracy: float | None = None
