#!/bin/bash
#
# 安装 Daily Pull 的 launchd 任务（支持 9:00 定时 + 醒来/登录后补跑）
#
# 用法: ./setup_launchd.sh
#
# 安装后会：
#   - 每天 9:00 若已登录则执行一次
#   - 每次登录/唤醒后若当天尚未执行则补跑一次
#   - 同一天内最多执行一次（由 run_daily_pull_once.sh 保证）
#
# 建议：安装本 launchd 后，从 crontab 中移除 Daily Pull 的 9:00 任务，避免重复执行。
#   删除 cron: crontab -e，删掉包含 daily_pull_testing_branches.py 的那一行
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLIST_NAME="com.prismax.daily_pull.plist"
SRC_PLIST="${SCRIPT_DIR}/${PLIST_NAME}"
LAUNCH_AGENTS="${HOME}/Library/LaunchAgents"
DST_PLIST="${LAUNCH_AGENTS}/${PLIST_NAME}"

# 检查 wrapper 和 plist 是否存在
[[ -f "${SCRIPT_DIR}/run_daily_pull_once.sh" ]] || { echo "错误: 找不到 run_daily_pull_once.sh"; exit 1; }
[[ -f "$SRC_PLIST" ]] || { echo "错误: 找不到 $PLIST_NAME"; exit 1; }

mkdir -p "$LAUNCH_AGENTS"

# 若已加载则先卸载
if launchctl list 2>/dev/null | grep -q com.prismax.daily_pull; then
    echo "正在卸载已有任务..."
    launchctl unload "$DST_PLIST" 2>/dev/null || true
fi

# 安装并加载
cp "$SRC_PLIST" "$DST_PLIST"
launchctl load "$DST_PLIST"

echo "✅ launchd 任务已安装并已加载"
echo ""
echo "说明:"
echo "  - 每天 9:00 会执行（若此时已登录）"
echo "  - 登录或唤醒后若当天尚未执行会补跑一次"
echo "  - 日志: ${SCRIPT_DIR}/daily_pull.log"
echo "  - launchd 自身输出: ${SCRIPT_DIR}/launchd_stdout.log, launchd_stderr.log"
echo ""
echo "⚠️  请从 crontab 中移除 Daily Pull 的 9:00 任务，避免同一天跑两次："
echo "   crontab -e  →  删除包含 daily_pull_testing_branches.py 的那一行"
echo ""
echo "常用命令:"
echo "  查看状态: launchctl list | grep prismax"
echo "  卸载:     launchctl unload $DST_PLIST"
echo "  重新加载: launchctl unload $DST_PLIST && launchctl load $DST_PLIST"
echo ""
