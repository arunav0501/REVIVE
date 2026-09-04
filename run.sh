#!/usr/bin/env bash

# ==============================================================================
# RecoverAI — Autonomous AR Follow-Up & Revenue Cycle AI Platform
# Unified All-in-One Startup Script
# ==============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "======================================================================"
echo " Starting RecoverAI System"
echo " Project Directory: $PROJECT_ROOT"
echo "======================================================================"

# 1. Environment & Dependency Checks
echo "[1/4] Checking environment & dependencies..."

if ! command -v python3 &>/dev/null; then
    echo "❌ Error: python3 is required but not installed." >&2
    exit 1
fi

if ! command -v npm &>/dev/null; then
    echo "❌ Error: npm/node is required but not installed." >&2
    exit 1
fi

# 2. Backend Setup
echo "[2/4] Verifying backend virtual environment..."
if [ ! -d "backend/.venv" ]; then
    echo "   -> Creating Python virtual environment in backend/.venv..."
    python3 -m venv backend/.venv
    backend/.venv/bin/pip install --upgrade pip
    backend/.venv/bin/pip install -r backend/requirements.txt
elif [ ! -f "backend/.venv/bin/uvicorn" ]; then
    echo "   -> Installing backend dependencies..."
    backend/.venv/bin/pip install -r backend/requirements.txt
fi

# 3. Frontend Setup
echo "[3/4] Verifying frontend node modules..."
if [ ! -d "frontend/node_modules" ]; then
    echo "   -> Installing frontend npm packages..."
    (cd frontend && npm install)
fi

# 4. Process Management & Cleanup Handler
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
    echo ""
    echo "======================================================================"
    echo " Shutting down RecoverAI services..."
    echo "======================================================================"
    if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
    if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi
    wait 2>/dev/null || true
    echo "✓ All services stopped cleanly."
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# 5. Launch Backend (FastAPI on Port 8000)
echo "[4/4] Starting backend and frontend servers..."
PYTHONPATH=. "$PROJECT_ROOT/backend/.venv/bin/uvicorn" backend.app.main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to respond to health check
echo "   -> Waiting for backend to initialize on http://127.0.0.1:8000/health..."
for i in {1..30}; do
    if curl -s http://127.0.0.1:8000/health | grep -q '"status":"healthy"' 2>/dev/null; then
        echo "   ✓ Backend ready!"
        break
    fi
    sleep 0.5
done

# 6. Launch Frontend (Vite on Port 5173)
(cd frontend && npm run dev -- --host 127.0.0.1 --port 5173) &
FRONTEND_PID=$!

echo ""
echo "======================================================================"
echo " RecoverAI is LIVE and ready!"
echo "   - Frontend UI:       http://localhost:5173"
echo "   - Backend API:       http://127.0.0.1:8000"
echo "   - Swagger API Docs:  http://127.0.0.1:8000/docs"
echo "   - Health Endpoint:   http://127.0.0.1:8000/health"
echo "======================================================================"
echo "Press Ctrl+C at any time to stop all services."
echo ""

# Wait for background processes to keep script running in foreground
wait
