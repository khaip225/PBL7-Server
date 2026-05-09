from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..services.metrics_service import MetricsService
from ..schemas.metrics import ConvergenceData
from ..schemas.metrics import OverviewMetrics

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/job/{job_id}")
async def get_job_metrics(job_id: str, db: AsyncSession = Depends(get_db)):
    svc = MetricsService(db)
    rounds = await svc.get_job_rounds(UUID(job_id))
    return {"job_id": job_id, "rounds": rounds}


@router.get("/job/{job_id}/convergence", response_model=ConvergenceData)
async def get_convergence(job_id: str, db: AsyncSession = Depends(get_db)):
    svc = MetricsService(db)
    data = await svc.get_convergence(UUID(job_id))
    return ConvergenceData(**data)


@router.get("/job/{job_id}/communication")
async def get_communication(job_id: str, db: AsyncSession = Depends(get_db)):
    svc = MetricsService(db)
    return await svc.get_communication_stats(UUID(job_id))


@router.get("/overview", response_model=OverviewMetrics)
async def get_overview(db: AsyncSession = Depends(get_db)):
    svc = MetricsService(db)
    data = await svc.get_overview()
    return OverviewMetrics(**data)


@router.get("/compare")
async def compare_jobs(job_ids: str = Query(...), db: AsyncSession = Depends(get_db)):
    ids = [UUID(jid.strip()) for jid in job_ids.split(",") if jid.strip()]
    svc = MetricsService(db)
    return await svc.compare_jobs(ids)
