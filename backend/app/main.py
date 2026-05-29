import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .database import engine, Base, async_session
from .api.router import api_router
from .api.auth import router as auth_router
from .websocket.manager import ws_manager
from .websocket.events import WSEvent
from .services.flower_manager import flower_manager, set_flower_manager_db_factory
from .services.settings_service import SettingsService
from .services.auth_service import seed_default_admin
from .services.client_service import ClientService
from shared.types import WSEventType

settings = get_settings()


async def _stale_client_monitor():
    """Background task: mark clients OFFLINE if they miss heartbeat."""
    while True:
        try:
            async with async_session() as db:
                svc = ClientService(db)
                stale = await svc.mark_stale_offline(settings.CLIENT_TIMEOUT_SECONDS)
                if stale > 0:
                    print(f"[StaleMonitor] Marked {stale} client(s) offline")
        except Exception as e:
            print(f"[StaleMonitor] Error: {e}")
        await asyncio.sleep(30)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed default settings
    async with async_session() as db:
        svc = SettingsService(db)
        await svc.seed_defaults()

    # Seed default admin user
    async with async_session() as db:
        await seed_default_admin(db, settings)

    # Wire DB factory to flower manager
    set_flower_manager_db_factory(async_session)

    # Start stale client monitor
    monitor_task = asyncio.create_task(_stale_client_monitor())

    yield

    # Shutdown: stop all Flower processes + monitor
    monitor_task.cancel()
    await flower_manager.shutdown_all()
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(o) for o in settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth routes (unprotected)
app.include_router(auth_router)

# Protected API routes
app.include_router(api_router)


@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "active_ws_connections": ws_manager.active_count,
        "running_jobs": flower_manager.running_count,
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    session_id = await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action", "")
            if action == "subscribe":
                job_id = data.get("job_id")
                await ws_manager.subscribe(session_id, job_id)
            elif action == "unsubscribe":
                job_id = data.get("job_id")
                if job_id:
                    await ws_manager.unsubscribe(session_id, job_id)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        await ws_manager.disconnect(session_id)
