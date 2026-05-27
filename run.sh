#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

if [ ! -d backend/.venv ]; then
  echo "Error: backend/.venv not found. Run ./setup.sh first."
  exit 1
fi

if [ ! -f backend/.env ]; then
  echo "Error: backend/.env not found. Run ./setup.sh first, then add your Anthropic API key."
  exit 1
fi

KEY=$(grep -E '^ANTHROPIC_API_KEY=' backend/.env | head -1 | cut -d '=' -f2- | tr -d '"' | tr -d "'" | xargs || true)
if [ -z "$KEY" ] || [ "$KEY" = "sk-ant-your-key-here" ]; then
  echo "Error: set a real ANTHROPIC_API_KEY in backend/.env (it is still empty or the placeholder from .env.example)."
  exit 1
fi

cleanup() {
  echo ""
  echo "Shutting down..."
  pkill -P "$FRONTEND_PID" 2>/dev/null || true
  pkill -P "$BACKEND_PID" 2>/dev/null || true
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup INT TERM

echo "Starting backend at http://localhost:8000 (interactive API docs at http://localhost:8000/docs)"
( cd backend && exec .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 ) &
BACKEND_PID=$!

echo "Starting frontend at http://localhost:5173"
( cd frontend && exec npm run dev ) &
FRONTEND_PID=$!

echo ""
echo "Both servers are starting."
echo "Open the frontend in your browser. If port 5173 was taken, Vite prints the actual URL it chose in the output above - use that one."
echo "Press Ctrl-C to stop both servers."
echo ""

wait
