import asyncio
import json
import os
import signal
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.training_job import TrainingJob
from ..models.round import Round
from ..models.checkpoint import Checkpoint
from ..flower_bridge.log_parser import FlowerLogParser
from ..websocket.manager import ws_manager
from ..websocket.events import WSEvent
from shared.types import WSEventType, EventSeverity, JobStatus
from shared.config import TASK_CONFIG


class FlowerProcess:
    def __init__(self, job_id: uuid.UUID, process: asyncio.subprocess.Process, config_path: Path):
        self.job_id = job_id
        self.process = process
        self.config_path = config_path


class FlowerProcessManager:
    def __init__(self, db_factory):
        self._running: dict[uuid.UUID, FlowerProcess] = {}
        self._db_factory = db_factory
        self._monitor_tasks: dict[uuid.UUID, list[asyncio.Task]] = {}

    @property
    def running_count(self) -> int:
        return len(self._running)

    def is_running(self, job_id: uuid.UUID) -> bool:
        return job_id in self._running

    async def start_job(self, job: TrainingJob, pretrained_override: str | None = None) -> FlowerProcess:
        cfg = TASK_CONFIG[job.task_type.value]
        port = job.flower_config.get("port", cfg["default_port"])
        pretrained = pretrained_override or job.model_config.get("pretrained_path") or cfg["default_pretrained"]

        # Write runtime config
        config_path = Path("flower_server") / "run_config.json"
        config_path.parent.mkdir(exist_ok=True)
        run_config = {
            "job_id": str(job.id),
            "task_type": job.task_type.value,
            "strategy": job.strategy.value,
            "strategy_params": job.strategy_params,
            "min_samples": job.min_samples,
            "pretrained_path": pretrained,
        }
        config_path.write_text(json.dumps(run_config, indent=2))

        # Build command
        cmd = [
            sys.executable, "flower_server/server.py",
            "--task", job.task_type.value,
            "--rounds", str(job.num_rounds),
            "--min-fit-clients", str(job.min_clients),
            "--min-available-clients", str(job.min_clients),
            "--port", str(port),
            "--min-samples", str(job.min_samples),
            "--config-path", str(config_path),
            "--job-id", str(job.id),
        ]
        if pretrained:
            cmd.extend(["--pretrained", pretrained])

        fl_mode = cfg.get("fl_mode")
        if fl_mode:
            cmd.extend(["--fl-mode", fl_mode])

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        fp = FlowerProcess(job_id=job.id, process=process, config_path=config_path)
        self._running[job.id] = fp

        # Start monitoring tasks
        self._monitor_tasks[job.id] = [
            asyncio.create_task(self._monitor_stdout(fp)),
            asyncio.create_task(self._monitor_stderr(fp)),
            asyncio.create_task(self._monitor_exit(fp)),
        ]

        # Update DB
        async with self._db_factory() as db:
            j = await db.get(TrainingJob, job.id)
            if j:
                j.status = JobStatus.RUNNING
                j.pid = process.pid
                j.started_at = datetime.now(timezone.utc)
                await db.commit()

        await ws_manager.broadcast(WSEvent(
            type=WSEventType.JOB_STARTED,
            payload={"job_id": str(job.id), "name": job.name, "task_type": job.task_type.value, "pid": process.pid}
        ))

        return fp

    async def stop_job(self, job_id: uuid.UUID, graceful: bool = True) -> bool:
        fp = self._running.get(job_id)
        if not fp:
            return False

        sig = signal.SIGTERM if graceful else signal.SIGKILL
        try:
            fp.process.send_signal(sig)
            try:
                await asyncio.wait_for(fp.process.wait(), timeout=30)
            except asyncio.TimeoutError:
                if graceful:
                    fp.process.kill()
                    await fp.process.wait()
        except ProcessLookupError:
            pass

        await self._cleanup(job_id, "stopped" if graceful else "killed")
        return True

    async def _monitor_stdout(self, fp: FlowerProcess):
        parser = FlowerLogParser(job_id=fp.job_id)
        try:
            while True:
                line = await fp.process.stdout.readline()
                if not line:
                    break
                decoded = line.decode("utf-8", errors="replace").strip()
                if decoded:
                    await parser.feed_line(decoded)
        except asyncio.CancelledError:
            pass

    async def _monitor_stderr(self, fp: FlowerProcess):
        try:
            while True:
                line = await fp.process.stderr.readline()
                if not line:
                    break
                decoded = line.decode("utf-8", errors="replace").strip()
                if decoded:
                    parser = FlowerLogParser(job_id=fp.job_id)
                    await parser._emit(WSEventType.ERROR_EVENT, {"message": decoded, "stream": "stderr"}, EventSeverity.ERROR)
        except asyncio.CancelledError:
            pass

    async def _monitor_exit(self, fp: FlowerProcess):
        returncode = await fp.process.wait()
        if returncode == 0:
            await self._on_job_finished(fp.job_id)
        else:
            await self._on_job_failed(fp.job_id, returncode)

    async def _on_job_finished(self, job_id: uuid.UUID):
        async with self._db_factory() as db:
            job = await db.get(TrainingJob, job_id)
            if job:
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now(timezone.utc)
                await db.commit()

        await ws_manager.broadcast(WSEvent(
            type=WSEventType.JOB_COMPLETED,
            payload={"job_id": str(job_id), "message": "Training completed successfully"}
        ))
        await self._cleanup(job_id, "completed")

    async def _on_job_failed(self, job_id: uuid.UUID, returncode: int):
        async with self._db_factory() as db:
            job = await db.get(TrainingJob, job_id)
            if job:
                job.status = JobStatus.FAILED
                job.completed_at = datetime.now(timezone.utc)
                await db.commit()

        await ws_manager.broadcast(WSEvent(
            type=WSEventType.JOB_FAILED,
            payload={"job_id": str(job_id), "returncode": returncode, "message": f"Flower process exited with code {returncode}"}
        ))
        await self._cleanup(job_id, "failed")

    async def _cleanup(self, job_id: uuid.UUID, reason: str):
        self._running.pop(job_id, None)
        tasks = self._monitor_tasks.pop(job_id, [])
        for task in tasks:
            task.cancel()

        # Clean up config file
        try:
            Path("flower_server/run_config.json").unlink(missing_ok=True)
        except Exception:
            pass

    async def shutdown_all(self):
        for job_id in list(self._running.keys()):
            await self.stop_job(job_id, graceful=True)


# Singleton
flower_manager = FlowerProcessManager(None)


def set_flower_manager_db_factory(factory):
    flower_manager._db_factory = factory
