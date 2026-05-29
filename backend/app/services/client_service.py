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
        # UPSERT by client_name — one hospital = one client
        q = select(Client).where(Client.client_name == data.client_name)
        result = await self.db.execute(q)
        existing = result.scalar_one_or_none()

        if existing:
            existing.client_host = data.client_host
            if data.task_type is not None:
                existing.task_type = data.task_type
            existing.hardware_info = data.hardware_info or existing.hardware_info
            existing.dataset_info = data.dataset_info or existing.dataset_info
            existing.status = ClientStatus.ONLINE
            await self.db.commit()
            await self.db.refresh(existing)
            return existing

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
        if data.task_type is not None:
            client.task_type = data.task_type
        if data.dataset_info:
            client.dataset_info = data.dataset_info
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

    async def mark_stale_offline(self, timeout_seconds: int = 60) -> int:
        """Mark clients as OFFLINE if no heartbeat within timeout_seconds."""
        cutoff = datetime.now(timezone.utc)
        # Use Python to filter (SQLAlchemy can't easily add timedelta in all DBs)
        q = select(Client).where(
            Client.status.in_([ClientStatus.ONLINE, ClientStatus.TRAINING, ClientStatus.IDLE])
        )
        result = await self.db.execute(q)
        stale_clients = [
            c for c in result.scalars().all()
            if c.last_heartbeat is None
            or (cutoff - c.last_heartbeat).total_seconds() > timeout_seconds
        ]
        for client in stale_clients:
            client.status = ClientStatus.OFFLINE
        if stale_clients:
            await self.db.commit()
        return len(stale_clients)

    async def get_overview_stats(self) -> dict:
        total = (await self.db.execute(select(func.count()).select_from(Client))).scalar() or 0
        online = (await self.db.execute(select(func.count()).where(Client.status == ClientStatus.ONLINE))).scalar() or 0
        return {"total_clients": total, "online_clients": online}
