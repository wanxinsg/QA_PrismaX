#!/usr/bin/env bash
set -euo pipefail

# Configuration
TEST_ENV_DIR="/Users/wanxin/PycharmProjects/Prismax/QA_PrismaX/Test_Env"
BACKEND_DIR="/Users/wanxin/PycharmProjects/Prismax/app-prismax-rp-backend/app_prismax_tele_op_services"
ALLURE_RESULTS_DIR="$TEST_ENV_DIR/test_report/allure-results"
BACKEND_LOG="$TEST_ENV_DIR/backend.log"

# Defaults (can be overridden by env)
# Hardcoded test target (requested)
TELE_HOST="localhost"
TELE_PORT="8081"
ROBOT_ID="arm1"
GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT:-thepinai}"
GOOGLE_APPLICATION_CREDENTIALS="${GOOGLE_APPLICATION_CREDENTIALS:-/Users/wanxin/PycharmProjects/Prismax/thepinai-compute-key.json}"

# Required credentials for tests
USER_ID="1001047"
TOKEN="QhZewTLifPlcp8I01ZFwCND7F1lKOolpFlbq1fdNA0s"

# Note: Values are hardcoded for convenience per request. Remove above and restore env reads for flexibility.

echo "==> Using Tele-Op backend: http://${TELE_HOST}:${TELE_PORT} robotId=${ROBOT_ID}"

wait_for_engineio() {
  local host="$1"
  local port="$2"
  local max_wait="${3:-60}"
  local url="http://${host}:${port}/socket.io/?EIO=4&transport=polling"
  echo "==> Waiting for Engine.IO at ${url} (timeout ${max_wait}s)..."
  local start_ts
  start_ts="$(date +%s)"
  while true; do
    if curl -s -m 2 -o /dev/null -w "%{http_code}" "$url" | grep -qE "200|204"; then
      echo "==> Engine.IO endpoint is up."
      return 0
    fi
    local now_ts
    now_ts="$(date +%s)"
    if (( now_ts - start_ts >= max_wait )); then
      echo "ERROR: Engine.IO endpoint did not become ready within ${max_wait}s."
      return 1
    fi
    sleep 1
  done
}

start_backend_if_needed() {
  if wait_for_engineio "$TELE_HOST" "$TELE_PORT" 1; then
    echo "==> Backend already running; skipping start."
    return 0
  fi

  echo "==> Starting backend in background... Logs: $BACKEND_LOG"
  # Use bash -lc to ensure 'source' is available and venv activation works
  nohup bash -lc "cd \"$BACKEND_DIR\" && \
    source .venv/bin/activate && \
    TEST_MODE=true GOOGLE_CLOUD_PROJECT=\"$GOOGLE_CLOUD_PROJECT\" \
    GOOGLE_APPLICATION_CREDENTIALS=\"$GOOGLE_APPLICATION_CREDENTIALS\" \
    PORT=\"$TELE_PORT\" python app.py" \
    > \"$BACKEND_LOG\" 2>&1 &

  # Wait up to 90s for server to become ready
  wait_for_engineio "$TELE_HOST" "$TELE_PORT" 90
}

run_tests() {
  echo "==> Running pytest and collecting Allure results into $ALLURE_RESULTS_DIR"
  mkdir -p "$ALLURE_RESULTS_DIR"
  TELE_HOST="$TELE_HOST" TELE_PORT="$TELE_PORT" ROBOT_ID="$ROBOT_ID" USER_ID="$USER_ID" TOKEN="$TOKEN" \
    python3 -m pytest -q "$TEST_ENV_DIR" --alluredir="$ALLURE_RESULTS_DIR"
}

open_allure_report() {
  if command -v allure >/dev/null 2>&1; then
    echo "==> Launching Allure report server..."
    allure serve "$ALLURE_RESULTS_DIR"
  else
    echo "==> Allure CLI not found."
    echo "Install with one of the following and rerun this script:"
    echo "  brew install allure"
    echo "  # or"
    echo "  npm i -g allure-commandline"
    echo "Allure results are at: $ALLURE_RESULTS_DIR"
  fi
}

main() {
  start_backend_if_needed
  run_tests
  open_allure_report
}

main "$@"


