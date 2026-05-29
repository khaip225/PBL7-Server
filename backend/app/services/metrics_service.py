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
            return {
                "job_id": str(job_id), "rounds": [], "best_loss": None,
                "best_accuracy": None, "best_auroc": None, "best_round": None,
            }

        losses = [r.loss for r in rounds if r.loss is not None]
        accuracies = [r.accuracy for r in rounds if r.accuracy is not None]
        aurocs = [r.auroc_macro for r in rounds if r.auroc_macro is not None]

        best_loss = min(losses) if losses else None
        best_accuracy = max(accuracies) if accuracies else None
        best_auroc = max(aurocs) if aurocs else None

        # Best round by AUROC if available, else by accuracy
        if best_auroc and aurocs:
            best_round = rounds[aurocs.index(best_auroc)].round_number
        elif best_accuracy and accuracies:
            best_round = rounds[accuracies.index(best_accuracy)].round_number
        else:
            best_round = None

        return {
            "job_id": str(job_id),
            "rounds": rounds,
            "best_loss": best_loss,
            "best_accuracy": best_accuracy,
            "best_auroc": best_auroc,
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
                "loss": r.loss,
                "auroc_macro": r.auroc_macro,
            })
        return {"job_id": str(job_id), "rounds": data}

    async def get_prototype_evolution(self, job_id: uuid.UUID) -> dict | None:
        """Extract prototype similarity evolution from rounds data."""
        rounds = await self.get_job_rounds(job_id)
        if not rounds:
            return None

        rounds_with_proto = [r for r in rounds if r.prototype_data is not None]
        if not rounds_with_proto:
            return None

        round_numbers = []
        ontology_alignment = []
        positive_similarity = []
        negative_similarity = []
        similarity_matrices = []

        import numpy as np

        for r in rounds_with_proto:
            pd = r.prototype_data or {}
            round_numbers.append(r.round_number)

            sim_matrix = pd.get("similarity_matrix", [])
            if sim_matrix:
                similarity_matrices.append(sim_matrix)

            # Parse from per-round prototype data
            pos_pairs = pd.get("positive_pairs", {})
            neg_pairs = pd.get("negative_pairs", {})

            if pos_pairs and neg_pairs:
                pos_mean = sum(pos_pairs.values()) / len(pos_pairs) if pos_pairs else 0
                neg_mean = sum(neg_pairs.values()) / len(neg_pairs) if neg_pairs else 0
                ontology_alignment.append(pos_mean - neg_mean)
                positive_similarity.append(pos_mean)
                negative_similarity.append(neg_mean)
            elif sim_matrix:
                # Compute from similarity matrix: indices 0,1,2=image, 3,4=audio (Crackle, Wheeze)
                arr = np.array(sim_matrix)
                if arr.shape == (5, 5):
                    # Positive: Crackle(3)-Pneumonia(0), Crackle(3)-Fibrosis(2), Wheeze(4)-COPD(1)
                    pos = (arr[3, 0] + arr[3, 2] + arr[4, 1]) / 3
                    # Negative: Crackle(3)-COPD(1), Wheeze(4)-Pneumonia(0), Wheeze(4)-Fibrosis(2)
                    neg = (arr[3, 1] + arr[4, 0] + arr[4, 2]) / 3
                    ontology_alignment.append(float(pos - neg))
                    positive_similarity.append(float(pos))
                    negative_similarity.append(float(neg))

        return {
            "job_id": str(job_id),
            "rounds": round_numbers,
            "ontology_alignment": ontology_alignment,
            "positive_similarity": positive_similarity,
            "negative_similarity": negative_similarity,
            "similarity_matrix": similarity_matrices,
        }

    async def get_overview(self) -> dict:
        total_clients = (await self.db.execute(select(func.count()).select_from(Client))).scalar() or 0
        online = (await self.db.execute(select(func.count()).where(Client.status == ClientStatus.ONLINE))).scalar() or 0
        active_jobs = (await self.db.execute(select(func.count()).where(TrainingJob.status == JobStatus.RUNNING))).scalar() or 0
        completed_jobs = (await self.db.execute(select(func.count()).where(TrainingJob.status == JobStatus.COMPLETED))).scalar() or 0
        total_checkpoints = (await self.db.execute(select(func.count()).select_from(Checkpoint))).scalar() or 0

        best_accuracy = (await self.db.execute(
            select(func.max(Round.accuracy))
        )).scalar()

        best_auroc = (await self.db.execute(
            select(func.max(Round.auroc_macro))
        )).scalar()

        return {
            "total_clients": total_clients,
            "online_clients": online,
            "active_jobs": active_jobs,
            "completed_jobs": completed_jobs,
            "total_checkpoints": total_checkpoints,
            "best_accuracy": best_accuracy,
            "best_auroc": best_auroc,
        }

    async def compare_jobs(self, job_ids: list[uuid.UUID]) -> dict:
        result = {}
        for jid in job_ids:
            conv = await self.get_convergence(jid)
            result[str(jid)] = conv
        return result
