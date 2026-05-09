import os
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..models.checkpoint import Checkpoint


class ModelService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_checkpoints(self, job_id: uuid.UUID | None = None, is_best: bool | None = None, page: int = 1, limit: int = 20) -> tuple[list[Checkpoint], int]:
        q = select(Checkpoint)
        if job_id:
            q = q.where(Checkpoint.job_id == job_id)
        if is_best is not None:
            q = q.where(Checkpoint.is_best == is_best)

        count_q = select(func.count()).select_from(q.subquery())
        total = (await self.db.execute(count_q)).scalar() or 0

        q = q.order_by(Checkpoint.created_at.desc()).offset((page - 1) * limit).limit(limit)
        checkpoints = list((await self.db.execute(q)).scalars().all())
        return checkpoints, total

    async def get_checkpoint(self, checkpoint_id: uuid.UUID) -> Checkpoint | None:
        return await self.db.get(Checkpoint, checkpoint_id)

    async def activate(self, checkpoint_id: uuid.UUID) -> Checkpoint | None:
        cp = await self.db.get(Checkpoint, checkpoint_id)
        if not cp or not os.path.exists(cp.file_path):
            return None

        # Deactivate all for this job
        await self.db.execute(
            Checkpoint.__table__.update().where(Checkpoint.job_id == cp.job_id).values(is_active=False)
        )
        cp.is_active = True
        await self.db.commit()
        await self.db.refresh(cp)
        return cp

    async def delete(self, checkpoint_id: uuid.UUID) -> bool:
        cp = await self.db.get(Checkpoint, checkpoint_id)
        if not cp:
            return False
        if os.path.exists(cp.file_path):
            os.remove(cp.file_path)
        await self.db.delete(cp)
        await self.db.commit()
        return True

    async def get_file_path(self, checkpoint_id: uuid.UUID) -> str | None:
        cp = await self.db.get(Checkpoint, checkpoint_id)
        if not cp or not os.path.exists(cp.file_path):
            return None
        return cp.file_path
