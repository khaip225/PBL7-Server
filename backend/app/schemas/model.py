from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class CheckpointResponse(BaseModel):
    id: UUID
    job_id: UUID
    round_number: int
    file_path: str
    file_size_bytes: int | None = None
    sha256_hash: str | None = None
    is_best: bool
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CheckpointListResponse(BaseModel):
    items: list[CheckpointResponse]
    total: int
    page: int
    limit: int
