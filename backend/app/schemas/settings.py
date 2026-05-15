from datetime import datetime
from pydantic import BaseModel


class SettingResponse(BaseModel):
    key: str
    value: dict
    description: str | None = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class SettingUpdate(BaseModel):
    value: dict
    description: str | None = None
