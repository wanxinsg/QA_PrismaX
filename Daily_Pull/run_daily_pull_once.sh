#!/usr/bin/env bash
#
# Daily Pull 每日最多执行一次包装脚本
# 供 launchd 使用：9:00 定时执行 + 登录/唤醒时补跑（若当天未跑过）
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATE_FILE="${SCRIPT_DIR}/.last_run_date"
ENV_FILE="${SCRIPT_DIR}/daily_pull_env.sh"
PYTHON_SCRIPT="${SCRIPT_DIR}/daily_pull_testing_branches.py"
LOG_FILE="${SCRIPT_DIR}/daily_pull.log"

TODAY=$(date +%Y-%m-%d)
if [[ -f "$STATE_FILE" ]] && [[ "$(cat "$STATE_FILE")" == "$TODAY" ]]; then
    # 今天已跑过，跳过
    exit 0
fi

[[ -f "$ENV_FILE" ]] || { echo "Missing $ENV_FILE"; exit 1; }
[[ -f "$PYTHON_SCRIPT" ]] || { echo "Missing $PYTHON_SCRIPT"; exit 1; }

# shellcheck source=./daily_pull_env.sh
source "$ENV_FILE"
cd "$SCRIPT_DIR"
/usr/bin/python3 "$PYTHON_SCRIPT" >> "$LOG_FILE" 2>&1
echo "$TODAY" > "$STATE_FILE"
