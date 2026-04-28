#!/bin/bash
#
# Prismax Git Pull 补跑脚本（与 Kira 同款）
# 在登录或唤醒后执行：若当天尚未执行过 pull，则运行一次 pull_repos.sh
# 配合 LaunchAgent 使用：登录时 (RunAtLoad) + 每 30 分钟检查一次
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAMP_FILE="$SCRIPT_DIR/.last_pull_date"
LOG_DIR="$SCRIPT_DIR/log"
CATCHUP_LOG="$LOG_DIR/catchup.log"

# Load environment (for LaunchAgent: no shell profile by default)
if [ -f ~/.zshrc ]; then
    source ~/.zshrc 2>/dev/null || true
fi

# Load Prismax env file(s) if present
ENV_FILE="$SCRIPT_DIR/daily_pull_env.sh"
ENV_LOCAL="$SCRIPT_DIR/daily_pull_env.local.sh"
if [ -f "$ENV_FILE" ]; then
    # shellcheck source=/dev/null
    source "$ENV_FILE"
fi
if [ -f "$ENV_LOCAL" ]; then
    # shellcheck source=/dev/null
    source "$ENV_LOCAL"
fi

mkdir -p "$LOG_DIR"
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$CATCHUP_LOG"
}

TODAY=$(date '+%Y-%m-%d')
if [ -f "$STAMP_FILE" ]; then
    LAST=$(cat "$STAMP_FILE" 2>/dev/null || true)
    if [ -n "$LAST" ] && [ "$LAST" = "$TODAY" ]; then
        log "Skip: already ran today ($TODAY). No catch-up needed."
        exit 0
    fi
fi

# 补跑仅允许 09:30–22:00，避免 09:00 主触发同时发生导致发两封邮件
CURRENT_HOUR=$(date '+%H')
CURRENT_MIN=$(date '+%M')
if [ "$CURRENT_HOUR" -lt 9 ] || [ "$CURRENT_HOUR" -ge 22 ]; then
    log "Skip: outside allowed window (09:30–22:00), current time=${CURRENT_HOUR}:${CURRENT_MIN}. Will retry later."
    exit 0
fi
if [ "$CURRENT_HOUR" -eq 9 ] && [ "$CURRENT_MIN" -lt 30 ]; then
    log "Skip: 09:00 reserved for main trigger only (window 09:30–22:00), current time=${CURRENT_HOUR}:${CURRENT_MIN}. Will retry later."
    exit 0
fi

log "Today ($TODAY) not yet run. Starting pull_repos.sh (catch-up run)."
exec "$SCRIPT_DIR/pull_repos.sh"

