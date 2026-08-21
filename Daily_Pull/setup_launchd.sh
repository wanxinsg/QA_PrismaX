#!/bin/bash
#
# 安装 Daily Pull 的 launchd 任务（每天 9:00 主任务 + 每 30 分钟补跑检查）
#
# 用法: ./setup_launchd.sh
#
# plist 模板使用 __DAILY_PULL_DIR__ 占位符。安装时会替换成脚本当前目录，
# 因此移动 Daily_Pull 后重新运行本脚本即可更新所有 launchd 路径。
#
# 建议：安装本 launchd 后，从 crontab 中移除旧的 Daily Pull 任务，避免重复执行。
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAUNCH_AGENTS="${HOME}/Library/LaunchAgents"
DOMAIN="gui/$(id -u)"

PLIST_SPECS=(
    "com.prismax.daily_pull.plist|com.prismax.gitpull.daily.plist|com.prismax.gitpull.daily"
    "com.prismax.gitpull.catchup.plist|com.prismax.gitpull.catchup.plist|com.prismax.gitpull.catchup"
)

# 检查执行脚本
[[ -x "${SCRIPT_DIR}/pull_repos.sh" ]] || { echo "错误: pull_repos.sh 不存在或不可执行"; exit 1; }
[[ -x "${SCRIPT_DIR}/run_pull_if_needed.sh" ]] || { echo "错误: run_pull_if_needed.sh 不存在或不可执行"; exit 1; }

mkdir -p "$LAUNCH_AGENTS" "${SCRIPT_DIR}/log"

# 清理早期安装脚本可能创建的错误文件名。
LEGACY_PLIST="${LAUNCH_AGENTS}/com.prismax.daily_pull.plist"
launchctl bootout "$DOMAIN" "$LEGACY_PLIST" 2>/dev/null || true
rm -f "$LEGACY_PLIST"

for spec in "${PLIST_SPECS[@]}"; do
    IFS='|' read -r template_name installed_name label <<< "$spec"
    src_plist="${SCRIPT_DIR}/${template_name}"
    dst_plist="${LAUNCH_AGENTS}/${installed_name}"

    [[ -f "$src_plist" ]] || { echo "错误: 找不到 $src_plist"; exit 1; }

    # 先按 label 和旧 plist 路径卸载，保证目录移动后不会残留旧任务。
    launchctl bootout "${DOMAIN}/${label}" 2>/dev/null || true
    launchctl bootout "$DOMAIN" "$dst_plist" 2>/dev/null || true

    # 使用当前脚本目录生成可安装的 plist；& 需要转义以安全用于 sed replacement。
    escaped_dir=${SCRIPT_DIR//&/\\&}
    sed "s|__DAILY_PULL_DIR__|${escaped_dir}|g" "$src_plist" > "$dst_plist"
    plutil -lint "$dst_plist" >/dev/null
    launchctl bootstrap "$DOMAIN" "$dst_plist"
    echo "✅ 已安装并加载: $label"
done

echo ""
echo "说明:"
echo "  - 主任务每天 9:00 执行 pull_repos.sh"
echo "  - 补跑任务登录时及每 30 分钟检查一次，当天邮件成功后不再重复"
echo "  - 日志目录: ${SCRIPT_DIR}/log"
echo "  - 密钥可放在 daily_pull_env.local.sh（已 .gitignore）"
echo ""
echo "常用命令:"
echo "  查看状态: launchctl print ${DOMAIN}/com.prismax.gitpull.daily"
echo "  查看补跑: launchctl print ${DOMAIN}/com.prismax.gitpull.catchup"
echo "  路径再次移动后: 重新运行 ${SCRIPT_DIR}/setup_launchd.sh"
echo ""
