"""Seed database with initial test data."""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend.app.database import Base
from backend.app.models.client import Client
from backend.app.models.training_job import TrainingJob
from backend.app.models.setting import Setting
from shared.types import TaskType, ClientStatus, JobStatus, AggregationStrategy
from shared.config import DEFAULT_SETTINGS
import uuid

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://pbl7:pbl7_secret@localhost:5432/pbl7_fl")


async def seed():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as db:
        # Seed settings
        for key, value in DEFAULT_SETTINGS.items():
            existing = await db.get(Setting, key)
            if not existing:
                db.add(Setting(key=key, value={"v": value}, description="Default"))

        # Seed test clients
        test_clients = [
            Client(
                client_name="BV Cho Ray", client_host="192.168.1.10:8080",
                task_type=TaskType.IMAGE, status=ClientStatus.ONLINE,
                hardware_info={"cpu": "Intel i7", "gpu_name": "RTX 3060", "gpu_memory_gb": 12, "ram_total_gb": 32},
                dataset_info={"total_samples": 2500, "classes": ["Normal", "Pneumonia"]},
                fl_client_id=1,
            ),
            Client(
                client_name="BV Bach Mai", client_host="192.168.1.20:8080",
                task_type=TaskType.AUDIO, status=ClientStatus.ONLINE,
                hardware_info={"cpu": "Intel i5", "gpu_name": "GTX 1660", "gpu_memory_gb": 6, "ram_total_gb": 16},
                dataset_info={"total_samples": 1800, "classes": ["Normal", "Pneumonia"]},
                fl_client_id=2,
            ),
            Client(
                client_name="BV Da Nang", client_host="10.0.5.30:8081",
                task_type=TaskType.IMAGE, status=ClientStatus.OFFLINE,
                hardware_info={"cpu": "Intel i9", "gpu_name": "RTX 4090", "gpu_memory_gb": 24, "ram_total_gb": 64},
                dataset_info={"total_samples": 5000, "classes": ["Normal", "Pneumonia"]},
                fl_client_id=3,
            ),
            Client(
                client_name="BV Hue", client_host="10.0.5.40:8080",
                task_type=TaskType.AUDIO, status=ClientStatus.IDLE,
                hardware_info={"cpu": "Intel i7", "gpu_name": "RTX 3080", "gpu_memory_gb": 10, "ram_total_gb": 32},
                dataset_info={"total_samples": 3500, "classes": ["Normal", "Pneumonia"]},
                fl_client_id=4,
            ),
        ]
        for c in test_clients:
            db.add(c)

        # Seed a sample draft job
        sample_job = TrainingJob(
            name="Demo Image Training",
            task_type=TaskType.IMAGE,
            status=JobStatus.DRAFT,
            strategy=AggregationStrategy.FEDAVG,
            num_rounds=10,
            min_clients=2,
            min_samples=300,
            model_config={"lr": 1e-4, "batch_size": 16, "local_epochs": 2},
        )
        db.add(sample_job)

        await db.commit()
        print("Seeded: 4 clients, 1 draft job, default settings")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
