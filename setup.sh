#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "==> Checking prerequisites"
PYTHON_BIN=""
for cand in python3.13 python3.12 python3.11 python3; do
  if command -v "$cand" >/dev/null 2>&1 && "$cand" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
    PYTHON_BIN="$cand"
    break
  fi
done
if [ -z "$PYTHON_BIN" ]; then
  echo "Error: Python 3.11 or newer is required but was not found. Install it and re-run ./setup.sh"
  exit 1
fi
echo "    Python: $("$PYTHON_BIN" --version) ($PYTHON_BIN)"

if ! command -v node >/dev/null 2>&1; then
  echo "Error: Node.js 18 or newer is required but was not found. Install it and re-run ./setup.sh"
  exit 1
fi
NODE_MAJOR=$(node -v | sed 's/^v//' | cut -d. -f1)
if [ "$NODE_MAJOR" -lt 18 ]; then
  echo "Error: Node.js 18 or newer is required, but found $(node -v). Upgrade and re-run ./setup.sh"
  exit 1
fi
echo "    Node: $(node -v)"

echo "==> Setting up the Python virtual environment"
if [ ! -d backend/.venv ]; then
  echo "    Creating backend/.venv"
  "$PYTHON_BIN" -m venv backend/.venv
else
  echo "    backend/.venv already exists, skipping"
fi

echo "==> Installing backend dependencies"
source backend/.venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r backend/requirements.txt
echo "    Backend dependencies installed"

echo "==> Installing frontend dependencies"
if [ ! -d frontend/node_modules ]; then
  ( cd frontend && npm install )
else
  echo "    frontend/node_modules already exists, skipping (delete it to force a reinstall)"
fi

echo "==> Checking backend/.env"
if [ -f backend/.env ] && grep -q "ANTHROPIC_API_KEY" backend/.env; then
  echo "    backend/.env found"
else
  cp backend/.env.example backend/.env
  echo "    Created backend/.env from the template."
  echo "    IMPORTANT: open backend/.env and paste your Anthropic API key into ANTHROPIC_API_KEY before running ./run.sh"
fi

echo ""
echo "Setup complete. Run ./run.sh to start the app."
