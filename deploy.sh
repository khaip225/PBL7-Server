#!/usr/bin/env bash
# PBL7 Production Deploy Script
# Usage: ./deploy.sh [VPS_IP_OR_DOMAIN]
#
# Examples:
#   ./deploy.sh                          # local deploy
#   ./deploy.sh 192.168.1.100            # VPS by IP
#   ./deploy.sh pbl7.example.com         # VPS by domain

set -euo pipefail

VPS=${1:-localhost}
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo " PBL7 Server Deploy"
echo " Target: ${VPS}"
echo "========================================"

# ---- 1. Prepare .env ----
if [ ! -f .env ]; then
    echo "[1/4] Creating .env from .env.production..."
    cp .env.production .env
    # Auto-set VPS domain
    if [ "$VPS" != "localhost" ]; then
        sed -i "s|VPS_DOMAIN=.*|VPS_DOMAIN=http://${VPS}|" .env
        sed -i "s|NEXT_PUBLIC_API_URL=.*|NEXT_PUBLIC_API_URL=|" .env
    fi
    echo "  Edit .env to set DB_PASSWORD and other values."
else
    echo "[1/4] .env already exists, skipping."
fi

# ---- 2. Copy files to VPS ----
if [ "$VPS" != "localhost" ]; then
    echo "[2/4] Copying files to VPS..."
    rsync -avz --exclude 'node_modules' --exclude '__pycache__' --exclude '.git' \
        --exclude '*.pth' --exclude '*.pyc' --exclude 'venv' --exclude '.venv' \
        --exclude 'Local_Data' --exclude 'fl_data' \
        "$SCRIPT_DIR/" "root@${VPS}:/opt/pbl7-server/"
    echo "  Files copied. Now SSH to VPS and run:"
    echo "    ssh root@${VPS}"
    echo "    cd /opt/pbl7-server"
    echo "    ./deploy.sh localhost  # runs steps 3-4 on VPS"
else
    echo "[2/4] Local deploy, skipping rsync."
fi

# ---- 3. Docker Compose Up ----
echo "[3/4] Starting services..."
docker compose -f docker/docker-compose.prod.yml --env-file .env up -d --build

echo "[4/4] Waiting for services..."
sleep 8

# ---- 4. Health Check ----
echo ""
echo "========================================"
echo " Health Check"
echo "========================================"

if curl -sf http://localhost/api/health > /dev/null 2>&1; then
    echo "  Backend:  OK ($(curl -s http://localhost/api/health))"
else
    echo "  Backend:  FAILED"
fi

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo "  Frontend: OK (HTTP $HTTP_CODE)"
else
    echo "  Frontend: WARNING (HTTP $HTTP_CODE, may still be building...)"
fi

echo ""
echo "========================================"
echo " Deploy Complete"
echo " Dashboard: http://${VPS}"
echo " API Docs:  http://${VPS}/api/docs"
echo ""
echo " Useful commands:"
echo "   docker compose -f docker/docker-compose.prod.yml logs -f"
echo "   docker compose -f docker/docker-compose.prod.yml restart"
echo "   docker compose -f docker/docker-compose.prod.yml down"
echo "========================================"
