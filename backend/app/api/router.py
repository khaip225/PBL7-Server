from fastapi import APIRouter, Depends
from .clients import router as clients_router
from .jobs import router as jobs_router
from .metrics import router as metrics_router
from .models import router as models_router
from .settings import router as settings_router
from .events import router as events_router
from .dependencies import get_current_user

api_router = APIRouter(dependencies=[Depends(get_current_user)])
api_router.include_router(clients_router)
api_router.include_router(jobs_router)
api_router.include_router(metrics_router)
api_router.include_router(models_router)
api_router.include_router(settings_router)
api_router.include_router(events_router)
