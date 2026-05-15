from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..services.model_service import ModelService
from ..schemas.model import CheckpointResponse, CheckpointListResponse

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("", response_model=CheckpointListResponse)
async def list_checkpoints(
    job_id: str | None = Query(None),
    is_best: bool | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    svc = ModelService(db)
    items, total = await svc.list_checkpoints(
        job_id=UUID(job_id) if job_id else None,
        is_best=is_best,
        page=page, limit=limit
    )
    return CheckpointListResponse(
        items=[CheckpointResponse.model_validate(c) for c in items],
        total=total, page=page, limit=limit
    )


@router.get("/{checkpoint_id}", response_model=CheckpointResponse)
async def get_checkpoint(checkpoint_id: str, db: AsyncSession = Depends(get_db)):
    svc = ModelService(db)
    cp = await svc.get_checkpoint(UUID(checkpoint_id))
    if not cp:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    return CheckpointResponse.model_validate(cp)


@router.get("/{checkpoint_id}/download")
async def download_checkpoint(checkpoint_id: str, db: AsyncSession = Depends(get_db)):
    svc = ModelService(db)
    path = await svc.get_file_path(UUID(checkpoint_id))
    if not path:
        raise HTTPException(status_code=404, detail="Checkpoint file not found")
    return FileResponse(path, filename=path.split("/")[-1])


@router.post("/{checkpoint_id}/activate", response_model=CheckpointResponse)
async def activate_checkpoint(checkpoint_id: str, db: AsyncSession = Depends(get_db)):
    svc = ModelService(db)
    cp = await svc.activate(UUID(checkpoint_id))
    if not cp:
        raise HTTPException(status_code=404, detail="Checkpoint not found or file missing")
    return CheckpointResponse.model_validate(cp)


@router.delete("/{checkpoint_id}")
async def delete_checkpoint(checkpoint_id: str, db: AsyncSession = Depends(get_db)):
    svc = ModelService(db)
    deleted = await svc.delete(UUID(checkpoint_id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    return {"message": "Checkpoint deleted"}
