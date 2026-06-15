#!/bin/bash
set -e

echo "=== PBL7 FL Platform Setup ==="

# Backend
echo "Installing backend dependencies..."
cd backend
pip install -e ".[dev]" 2>/dev/null || pip install -r <(echo "fastapi uvicorn sqlalchemy asyncpg alembic pydantic pydantic-settings flwr torch torchvision httpx python-multipart aiofiles")
cd ..

# Frontend
echo "Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Docker
echo "Starting PostgreSQL..."
docker compose -f docker/docker-compose.yml up -d postgres

# Wait for DB
echo "Waiting for PostgreSQL..."
until docker compose -f docker/docker-compose.yml exec -T postgres pg_isready -U pbl7 2>/dev/null; do
  sleep 2
done

echo "Running DB init (tables created at app startup)..."
# TODO: Initialize Alembic when ready: cd backend && alembic init -t async && alembic upgrade head
python scripts/seed_db.py

echo "=== Setup complete ==="
echo "Run: docker compose -f docker/docker-compose.yml up"
