from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..services.job_service import JobService
from ..services.flower_manager import flower_manager
from ..schemas.job import JobCreate, JobUpdate, JobResponse, JobListResponse
from shared.types import JobStatus

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("", response_model=JobListResponse)
async def list_jobs(
    status: str | None = Query(None),
    task_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    svc = JobService(db)
    items, total = await svc.list_jobs(status=status, task_type=task_type, page=page, limit=limit)
    return JobListResponse(
        items=[JobResponse.model_validate(j) for j in items],
        total=total, page=page, limit=limit
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    svc = JobService(db)
    job = await svc.get_job(UUID(job_id))
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse.model_validate(job)


@router.post("", response_model=JobResponse, status_code=201)
async def create_job(data: JobCreate, db: AsyncSession = Depends(get_db)):
    svc = JobService(db)
    job = await svc.create(data)
    return JobResponse.model_validate(job)


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(job_id: str, data: JobUpdate, db: AsyncSession = Depends(get_db)):
    svc = JobService(db)
    job = await svc.update(UUID(job_id), data)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or not in draft status")
    return JobResponse.model_validate(job)


@router.post("/{job_id}/start")
async def start_job(job_id: str, db: AsyncSession = Depends(get_db)):
    svc = JobService(db)
    job = await svc.get_job(UUID(job_id))
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.DRAFT:
        raise HTTPException(status_code=400, detail=f"Cannot start job in {job.status.value} status")

    # Check concurrency limit
    from ..config import get_settings
    settings = get_settings()
    if flower_manager.running_count >= settings.MAX_CONCURRENT_JOBS:
        raise HTTPException(status_code=429, detail=f"Max {settings.MAX_CONCURRENT_JOBS} concurrent jobs allowed")

    try:
        fp = await flower_manager.start_job(job)
        return {"message": "Job started", "job_id": str(job.id), "pid": fp.process.pid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start job: {str(e)}")


@router.post("/{job_id}/stop")
async def stop_job(job_id: str):
    success = await flower_manager.stop_job(UUID(job_id), graceful=True)
    if not success:
        raise HTTPException(status_code=404, detail="Job not running")
    return {"message": "Job stopped", "job_id": job_id}


@router.delete("/{job_id}")
async def delete_job(job_id: str, db: AsyncSession = Depends(get_db)):
    svc = JobService(db)
    deleted = await svc.delete(UUID(job_id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Job not found or cannot be deleted while running")
    return {"message": "Job deleted"}


@router.get("/{job_id}/rounds")
async def get_job_rounds(job_id: str, db: AsyncSession = Depends(get_db)):
    svc = JobService(db)
    rounds = await svc.get_job_rounds(UUID(job_id))
    return rounds


@router.get("/{job_id}/progress")
async def get_job_progress(job_id: str, db: AsyncSession = Depends(get_db)):
    svc = JobService(db)
    progress = await svc.get_progress(UUID(job_id))
    if not progress:
        raise HTTPException(status_code=404, detail="Job not found")
    return progress
