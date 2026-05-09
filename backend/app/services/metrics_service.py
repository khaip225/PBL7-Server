import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..models.round import Round
from ..models.checkpoint import Checkpoint
from ..models.training_job import TrainingJob
from ..models.client import Client
from shared.types import JobStatus, ClientStatus


class MetricsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_job_rounds(self, job_id: uuid.UUID) -> list[Round]:
        q = select(Round).where(Round.job_id == job_id).order_by(Round.round_number)
        return list((await self.db.execute(q)).scalars().all())

    async def get_convergence(self, job_id: uuid.UUID) -> dict:
        rounds = await self.get_job_rounds(job_id)
        if not rounds:
            return {"job_id": str(job_id), "rounds": [], "best_loss": None, "best_accuracy": None, "best_round": None}

        losses = [r.loss for r in rounds if r.loss is not None]
        accuracies = [r.accuracy for r in rounds if r.accuracy is not None]
        best_loss = min(losses) if losses else None
        best_accuracy = max(accuracies) if accuracies else None
        best_round = rounds[accuracies.index(best_accuracy)].round_number if best_accuracy and accuracies else None

        return {
            "job_id": str(job_id),
            "rounds": rounds,
            "best_loss": best_loss,
            "best_accuracy": best_accuracy,
            "best_round": best_round,
        }

    async def get_communication_stats(self, job_id: uuid.UUID) -> dict:
        rounds = await self.get_job_rounds(job_id)
        data = []
        for r in rounds:
            data.append({
                "round_number": r.round_number,
                "num_clients": r.num_clients,
                "num_skipped": r.num_skipped,
                "duration_seconds": r.duration_seconds,
            })
        return {"job_id": str(job_id), "rounds": data}

    async def get_overview(self) -> dict:
        total_clients = (await self.db.execute(select(func.count()).select_from(Client))).scalar() or 0
        online = (await self.db.execute(select(func.count()).where(Client.status == ClientStatus.ONLINE))).scalar() or 0
        active_jobs = (await self.db.execute(select(func.count()).where(TrainingJob.status == JobStatus.RUNNING))).scalar() or 0
        completed_jobs = (await self.db.execute(select(func.count()).where(TrainingJob.status == JobStatus.COMPLETED))).scalar() or 0
        total_checkpoints = (await self.db.execute(select(func.count()).select_from(Checkpoint))).scalar() or 0

        best_accuracy = (await self.db.execute(
            select(func.max(Round.accuracy))
        )).scalar()

        return {
            "total_clients": total_clients,
            "online_clients": online,
            "active_jobs": active_jobs,
            "completed_jobs": completed_jobs,
            "total_checkpoints": total_checkpoints,
            "best_accuracy": best_accuracy,
        }

    async def compare_jobs(self, job_ids: list[uuid.UUID]) -> dict:
        result = {}
        for jid in job_ids:
            conv = await self.get_convergence(jid)
            result[str(jid)] = conv
        return result
