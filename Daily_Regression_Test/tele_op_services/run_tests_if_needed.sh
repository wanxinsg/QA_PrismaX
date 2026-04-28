#!/bin/bash
#
# Tele-Op Regression 补跑脚本
# 配合 LaunchAgent 使用：登录时 (RunAtLoad) + 每 30 分钟检查一次
# 若当天尚未执行过回归测试，且当前在合理时间窗口内（09:00–11:00），则补跑一次
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAMP_FILE="$SCRIPT_DIR/.last_regression_date"
PULL_SENT_AT_FILE="$SCRIPT_DIR/.daily_pull_sent_at"
LOG_DIR="$SCRIPT_DIR/log"
CATCHUP_LOG="$LOG_DIR/regression_catchup.log"

# LaunchAgent 默认不加载 shell profile，需手动 source
if [ -f ~/.zshrc ]; then
    source ~/.zshrc 2>/dev/null || true
fi

mkdir -p "$LOG_DIR"
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$CATCHUP_LOG"
}

TODAY=$(date '+%Y-%m-%d')
if [ -f "$STAMP_FILE" ]; then
    LAST=$(cat "$STAMP_FILE" 2>/dev/null)
    if [ -n "$LAST" ] && [ "$LAST" = "$TODAY" ]; then
        log "Skip: already ran today ($TODAY). No catch-up needed."
        exit 0
    fi
fi

# 必须严格依赖：Prismax 日报邮件发送成功时间 + 30 分钟
if [ ! -f "$PULL_SENT_AT_FILE" ]; then
    log "Skip: missing daily pull sent_at stamp ($PULL_SENT_AT_FILE). Will retry later."
    exit 0
fi

SENT_AT_RAW="$(cat "$PULL_SENT_AT_FILE" 2>/dev/null | tr -d '\r\n' || true)"
if [ -z "$SENT_AT_RAW" ]; then
    log "Skip: empty daily pull sent_at stamp ($PULL_SENT_AT_FILE). Will retry later."
    exit 0
fi

SENT_DATE="${SENT_AT_RAW%% *}"
if [ -z "$SENT_DATE" ] || [ "$SENT_DATE" != "$TODAY" ]; then
    log "Skip: sent_at date mismatch. sent_at='$SENT_AT_RAW' (need today=$TODAY)."
    exit 0
fi

# macOS: date -j -f "%Y-%m-%d %H:%M:%S" "..." +%s
SENT_EPOCH="$(date -j -f "%Y-%m-%d %H:%M:%S" "$SENT_AT_RAW" +%s 2>/dev/null || true)"
if [ -z "$SENT_EPOCH" ]; then
    log "Skip: cannot parse sent_at='$SENT_AT_RAW' (expect 'YYYY-MM-DD HH:MM:SS')."
    exit 0
fi

NOW_EPOCH="$(date +%s)"
READY_EPOCH="$((SENT_EPOCH + 1800))"
if [ "$NOW_EPOCH" -lt "$READY_EPOCH" ]; then
    WAIT_SEC="$((READY_EPOCH - NOW_EPOCH))"
    log "Skip: not ready yet. sent_at='$SENT_AT_RAW', wait ${WAIT_SEC}s (need +30min)."
    exit 0
fi

# 保险时间窗：避免深夜误触发（若日报很晚发送，仍允许在 22:00 前补跑）
CURRENT_HOUR=$(date '+%H')
if [ "$CURRENT_HOUR" -lt 9 ] || [ "$CURRENT_HOUR" -ge 22 ]; then
    log "Skip: outside allowed window (09:00–22:00), current hour=$CURRENT_HOUR. Will retry later."
    exit 0
fi

log "Ready (sent_at +30min). Starting run_tests_cron.sh."
if [ "${REGRESSION_DRY_RUN:-}" = "1" ]; then
    log "DRY_RUN=1: would run run_tests_cron.sh now. Exiting 0 without stamping."
    exit 0
fi

"$SCRIPT_DIR/run_tests_cron.sh" >> "$LOG_DIR/regression_catchup_stdout.log" 2>&1
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "$TODAY" > "$STAMP_FILE"
    log "Regression done. Stamped $STAMP_FILE."
else
    log "Regression failed (exit=$EXIT_CODE). Not stamping; will retry next interval."
fi
exit $EXIT_CODE
