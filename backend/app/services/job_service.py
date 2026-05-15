import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..models.training_job import TrainingJob
from ..models.round import Round
from ..schemas.job import JobCreate, JobUpdate
from shared.types import JobStatus


class JobService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_jobs(self, status: str | None = None, task_type: str | None = None, page: int = 1, limit: int = 20) -> tuple[list[TrainingJob], int]:
        q = select(TrainingJob)
        if status:
            q = q.where(TrainingJob.status == status)
        if task_type:
            q = q.where(TrainingJob.task_type == task_type)

        count_q = select(func.count()).select_from(q.subquery())
        total = (await self.db.execute(count_q)).scalar() or 0

        q = q.order_by(TrainingJob.created_at.desc()).offset((page - 1) * limit).limit(limit)
        jobs = list((await self.db.execute(q)).scalars().all())
        return jobs, total

    async def get_job(self, job_id: uuid.UUID) -> TrainingJob | None:
        return await self.db.get(TrainingJob, job_id)

    async def create(self, data: JobCreate) -> TrainingJob:
        d = data.model_dump()
        # Map schema field names to DB column names
        d["model_config"] = d.pop("model_cfg")
        d["flower_config"] = d.pop("flower_cfg")
        job = TrainingJob(**d)
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def update(self, job_id: uuid.UUID, data: JobUpdate) -> TrainingJob | None:
        job = await self.db.get(TrainingJob, job_id)
        if not job or job.status != JobStatus.DRAFT:
            return None
        update_data = data.model_dump(exclude_none=True)
        if "model_cfg" in update_data:
            update_data["model_config"] = update_data.pop("model_cfg")
        for k, v in update_data.items():
            setattr(job, k, v)
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def delete(self, job_id: uuid.UUID) -> bool:
        job = await self.db.get(TrainingJob, job_id)
        if not job or job.status == JobStatus.RUNNING:
            return False
        await self.db.delete(job)
        await self.db.commit()
        return True

    async def get_job_rounds(self, job_id: uuid.UUID) -> list[Round]:
        q = select(Round).where(Round.job_id == job_id).order_by(Round.round_number)
        return list((await self.db.execute(q)).scalars().all())

    async def get_progress(self, job_id: uuid.UUID) -> dict | None:
        job = await self.db.get(TrainingJob, job_id)
        if not job:
            return None
        completed = (await self.db.execute(
            select(func.count()).where(Round.job_id == job_id)
        )).scalar() or 0
        return {
            "job_id": str(job.id),
            "status": job.status.value,
            "current_round": job.current_round,
            "total_rounds": job.num_rounds,
            "rounds_completed": completed,
            "progress_pct": round(completed / job.num_rounds * 100, 1) if job.num_rounds > 0 else 0,
        }

    async def get_overview_stats(self) -> dict:
        active = (await self.db.execute(
            select(func.count()).where(TrainingJob.status == JobStatus.RUNNING)
        )).scalar() or 0
        completed = (await self.db.execute(
            select(func.count()).where(TrainingJob.status == JobStatus.COMPLETED)
        )).scalar() or 0
        return {"active_jobs": active, "completed_jobs": completed}
