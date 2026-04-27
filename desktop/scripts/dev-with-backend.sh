#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_ROOT="$(cd "${DESKTOP_DIR}/.." && pwd)"
BACKEND_URL="${AI_QA_BACKEND_URL:-http://127.0.0.1:8000}"
BACKEND_PID=""

cleanup() {
  if [[ -n "${BACKEND_PID}" ]]; then
    kill "${BACKEND_PID}" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT

if ! curl -fsS "${BACKEND_URL}/health" >/dev/null 2>&1; then
  echo "Starting FastAPI backend at ${BACKEND_URL}"
  cd "${PROJECT_ROOT}"
  if [[ -x ".venv/bin/python" ]]; then
    .venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
  else
    python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
  fi
  BACKEND_PID="$!"

  for _ in {1..40}; do
    if curl -fsS "${BACKEND_URL}/health" >/dev/null 2>&1; then
      break
    fi
    sleep 0.5
  done
fi

cd "${DESKTOP_DIR}"
npm run dev
