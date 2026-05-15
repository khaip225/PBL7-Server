import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..models.client import Client
from ..schemas.client import ClientCreate, ClientUpdate, ClientHeartbeat
from shared.types import ClientStatus


class ClientService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_clients(self, status: str | None = None, task_type: str | None = None, page: int = 1, limit: int = 20) -> tuple[list[Client], int]:
        q = select(Client)
        if status:
            q = q.where(Client.status == status)
        if task_type:
            q = q.where(Client.task_type == task_type)

        count_q = select(func.count()).select_from(q.subquery())
        total = (await self.db.execute(count_q)).scalar() or 0

        q = q.order_by(Client.updated_at.desc()).offset((page - 1) * limit).limit(limit)
        clients = list((await self.db.execute(q)).scalars().all())
        return clients, total

    async def get_client(self, client_id: uuid.UUID) -> Client | None:
        return await self.db.get(Client, client_id)

    async def register(self, data: ClientCreate) -> Client:
        client = Client(**data.model_dump(), status=ClientStatus.ONLINE)
        self.db.add(client)
        await self.db.commit()
        await self.db.refresh(client)
        return client

    async def update(self, client_id: uuid.UUID, data: ClientUpdate) -> Client | None:
        client = await self.db.get(Client, client_id)
        if not client:
            return None
        update_data = data.model_dump(exclude_none=True)
        for k, v in update_data.items():
            setattr(client, k, v)
        await self.db.commit()
        await self.db.refresh(client)
        return client

    async def heartbeat(self, client_id: uuid.UUID, data: ClientHeartbeat) -> Client | None:
        client = await self.db.get(Client, client_id)
        if not client:
            return None
        client.last_heartbeat = datetime.now(timezone.utc)
        client.latency_ms = data.latency_ms
        if client.status == ClientStatus.OFFLINE:
            client.status = ClientStatus.ONLINE
        if data.hardware_info:
            client.hardware_info = data.hardware_info
        await self.db.commit()
        await self.db.refresh(client)
        return client

    async def set_offline(self, client_id: uuid.UUID) -> Client | None:
        client = await self.db.get(Client, client_id)
        if not client:
            return None
        client.status = ClientStatus.OFFLINE
        client.last_heartbeat = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(client)
        return client

    async def delete(self, client_id: uuid.UUID) -> bool:
        client = await self.db.get(Client, client_id)
        if not client:
            return False
        await self.db.delete(client)
        await self.db.commit()
        return True

    async def get_overview_stats(self) -> dict:
        total = (await self.db.execute(select(func.count()).select_from(Client))).scalar() or 0
        online = (await self.db.execute(select(func.count()).where(Client.status == ClientStatus.ONLINE))).scalar() or 0
        return {"total_clients": total, "online_clients": online}
