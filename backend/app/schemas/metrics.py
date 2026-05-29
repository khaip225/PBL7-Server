from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class ClientRoundMetric(BaseModel):
    client_id: str
    client_name: str
    num_samples: int
    loss: float
    accuracy: float | None = None
    auroc_macro: float | None = None
    per_class_auroc: dict[str, float] = {}


class RoundMetricsResponse(BaseModel):
    id: UUID
    round_number: int
    loss: float | None = None
    accuracy: float | None = None
    auroc_macro: float | None = None
    per_class_auroc: dict[str, float] | None = None
    prototype_data: dict | None = None
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
    best_auroc: float | None = None
    best_round: int | None = None


class PrototypeEvolution(BaseModel):
    """Prototype similarity matrix evolution across rounds."""
    job_id: UUID
    rounds: list[int]
    ontology_alignment: list[float]  # pos_sim - neg_sim per round
    positive_similarity: list[float]  # mean of ontology-positive pairs
    negative_similarity: list[float]  # mean of ontology-negative pairs
    similarity_matrix: list[list[list[float]]]  # [round][5][5] cosine sim matrix


class OverviewMetrics(BaseModel):
    total_clients: int
    online_clients: int
    active_jobs: int
    completed_jobs: int
    total_checkpoints: int
    best_accuracy: float | None = None
    best_auroc: float | None = None
