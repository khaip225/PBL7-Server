from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from shared.types import TaskType, ClientStatus


class ClientCreate(BaseModel):
    client_name: str
    client_host: str
    task_type: TaskType
    hardware_info: dict = Field(default_factory=dict)
    dataset_info: dict = Field(default_factory=dict)


class ClientUpdate(BaseModel):
    client_name: str | None = None
    hardware_info: dict | None = None
    dataset_info: dict | None = None


class ClientHeartbeat(BaseModel):
    latency_ms: float = 0.0
    hardware_info: dict | None = None


class ClientResponse(BaseModel):
    id: UUID
    client_name: str
    client_host: str
    task_type: TaskType
    status: ClientStatus
    last_heartbeat: datetime | None = None
    hardware_info: dict
    dataset_info: dict
    fl_client_id: int | None = None
    latency_ms: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClientListResponse(BaseModel):
    items: list[ClientResponse]
    total: int
    page: int
    limit: int
