from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from shared.types import TaskType, JobStatus, AggregationStrategy


class ModelConfig(BaseModel):
    lr: float = 1e-4
    batch_size: int = 16
    local_epochs: int = 2
    pretrained_path: str | None = None
    mu: float = 0.001


class FlowerConfig(BaseModel):
    port: int | None = None


class JobCreate(BaseModel):
    name: str
    task_type: TaskType
    strategy: AggregationStrategy = AggregationStrategy.FEDAVG
    strategy_params: dict = Field(default_factory=dict)
    num_rounds: int = 10
    min_clients: int = 2
    min_samples: int = 300
    model_cfg: ModelConfig = Field(default_factory=ModelConfig)
    flower_cfg: dict = Field(default_factory=dict)


class JobUpdate(BaseModel):
    name: str | None = None
    num_rounds: int | None = None
    min_clients: int | None = None
    min_samples: int | None = None
    model_cfg: ModelConfig | None = None
    strategy_params: dict | None = None


class JobResponse(BaseModel):
    id: UUID
    name: str
    task_type: TaskType
    status: JobStatus
    strategy: AggregationStrategy
    strategy_params: dict
    num_rounds: int
    min_clients: int
    min_samples: int
    model_cfg: dict = Field(alias="model_config")
    flower_cfg: dict = Field(alias="flower_config")
    pid: int | None = None
    current_round: int
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class JobListResponse(BaseModel):
    items: list[JobResponse]
    total: int
    page: int
    limit: int
