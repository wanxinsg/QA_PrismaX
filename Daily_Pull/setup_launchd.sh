#!/bin/bash
#
# 安装 Daily Work 的 launchd 任务（工作日 9:30 + RunAtLoad 在 9:25–9:45 窗口内补跑）
#
# 用法: ./setup_launchd.sh
#
# 安装后会：
#   - 每周一至周五 9:30 若已登录则尝试执行
#   - 用户登录时（RunAtLoad）若处于 9:25–9:45 且当天尚未执行则补跑一次
#   - 同一天内最多执行一次（由 run_daily_pull_once.sh 保证）
#   - 周末不执行（run_daily_pull_once.sh 内 date +%u 判断）
#
# 建议：安装本 launchd 后，从 crontab 中移除旧的 Daily Pull 任务，避免重复执行。
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
echo "  - 工作日（周一至周五）每天 9:30 触发"
echo "  - 脚本仅在 9:25–9:45 内实际运行，且每天最多一次"
echo "  - 日志: ${SCRIPT_DIR}/daily_pull.log"
echo "  - launchd 自身输出: ${SCRIPT_DIR}/launchd_stdout.log, launchd_stderr.log"
echo "  - LLM 依赖: pip install -r ${SCRIPT_DIR}/requirements-daily-work.txt"
echo "  - 密钥可放在 daily_pull_env.local.sh（已 .gitignore）"
echo ""
echo "常用命令:"
echo "  查看状态: launchctl list | grep prismax"
echo "  卸载:     launchctl unload $DST_PLIST"
echo "  重新加载: launchctl unload $DST_PLIST && launchctl load $DST_PLIST"
echo ""
