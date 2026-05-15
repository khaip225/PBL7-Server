from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..services.client_service import ClientService
from ..schemas.client import ClientCreate, ClientUpdate, ClientHeartbeat, ClientResponse, ClientListResponse

router = APIRouter(prefix="/api/clients", tags=["clients"])


@router.get("", response_model=ClientListResponse)
async def list_clients(
    status: str | None = Query(None),
    task_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    svc = ClientService(db)
    items, total = await svc.list_clients(status=status, task_type=task_type, page=page, limit=limit)
    return ClientListResponse(
        items=[ClientResponse.model_validate(c) for c in items],
        total=total, page=page, limit=limit
    )


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(client_id: str, db: AsyncSession = Depends(get_db)):
    from uuid import UUID
    svc = ClientService(db)
    client = await svc.get_client(UUID(client_id))
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return ClientResponse.model_validate(client)


@router.post("/register", response_model=ClientResponse, status_code=201)
async def register_client(data: ClientCreate, db: AsyncSession = Depends(get_db)):
    svc = ClientService(db)
    client = await svc.register(data)
    return ClientResponse.model_validate(client)


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(client_id: str, data: ClientUpdate, db: AsyncSession = Depends(get_db)):
    from uuid import UUID
    svc = ClientService(db)
    client = await svc.update(UUID(client_id), data)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return ClientResponse.model_validate(client)


@router.post("/{client_id}/heartbeat", response_model=ClientResponse)
async def client_heartbeat(client_id: str, data: ClientHeartbeat, db: AsyncSession = Depends(get_db)):
    from uuid import UUID
    svc = ClientService(db)
    client = await svc.heartbeat(UUID(client_id), data)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return ClientResponse.model_validate(client)


@router.post("/{client_id}/offline", response_model=ClientResponse)
async def client_offline(client_id: str, db: AsyncSession = Depends(get_db)):
    from uuid import UUID
    svc = ClientService(db)
    client = await svc.set_offline(UUID(client_id))
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return ClientResponse.model_validate(client)


@router.delete("/{client_id}")
async def delete_client(client_id: str, db: AsyncSession = Depends(get_db)):
    from uuid import UUID
    svc = ClientService(db)
    deleted = await svc.delete(UUID(client_id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"message": "Client deleted"}
