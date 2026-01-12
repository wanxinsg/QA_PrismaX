#!/bin/bash
#
# 设置Daily Pull的Cron任务
#
# 用法:
#   ./setup_cron.sh [hour] [minute]
#
# 参数:
#   hour   - 运行时间的小时 (0-23, 默认: 9)
#   minute - 运行时间的分钟 (0-59, 默认: 0)
#
# 示例:
#   ./setup_cron.sh          # 每天9:00运行
#   ./setup_cron.sh 10 30    # 每天10:30运行
#

set -euo pipefail

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/daily_pull_env.sh"
PYTHON_SCRIPT="${SCRIPT_DIR}/daily_pull_testing_branches.py"
LOG_FILE="${SCRIPT_DIR}/daily_pull.log"

# 检查文件是否存在
if [ ! -f "$ENV_FILE" ]; then
    echo "错误: 找不到环境变量配置文件: $ENV_FILE"
    exit 1
fi

if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "错误: 找不到Python脚本: $PYTHON_SCRIPT"
    exit 1
fi

# 获取运行时间（默认9:00）
HOUR="${1:-9}"
MINUTE="${2:-0}"

# 验证时间参数
if ! [[ "$HOUR" =~ ^[0-9]+$ ]] || [ "$HOUR" -lt 0 ] || [ "$HOUR" -gt 23 ]; then
    echo "错误: 小时必须是0-23之间的数字"
    exit 1
fi

if ! [[ "$MINUTE" =~ ^[0-9]+$ ]] || [ "$MINUTE" -lt 0 ] || [ "$MINUTE" -gt 59 ]; then
    echo "错误: 分钟必须是0-59之间的数字"
    exit 1
fi

# 构建cron任务
CRON_TIME="$MINUTE $HOUR * * *"
CRON_COMMAND="source $ENV_FILE && cd $SCRIPT_DIR && /usr/bin/python3 $PYTHON_SCRIPT >> $LOG_FILE 2>&1"
CRON_ENTRY="$CRON_TIME $CRON_COMMAND"

# 检查是否已存在相同的cron任务
EXISTING_CRON=$(crontab -l 2>/dev/null | grep -F "$PYTHON_SCRIPT" || true)

if [ -n "$EXISTING_CRON" ]; then
    echo "⚠️  检测到已存在的cron任务:"
    echo "   $EXISTING_CRON"
    echo ""
    read -p "是否要替换现有任务? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "已取消操作"
        exit 0
    fi
    
    # 删除旧任务
    (crontab -l 2>/dev/null | grep -vF "$PYTHON_SCRIPT") | crontab -
    echo "✅ 已删除旧任务"
fi

# 添加新任务
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

echo "✅ Cron任务已设置成功！"
echo ""
echo "任务详情:"
echo "  时间: 每天 $HOUR:$MINUTE"
echo "  命令: $CRON_COMMAND"
echo "  日志: $LOG_FILE"
echo ""
echo "查看当前cron任务:"
echo "  crontab -l"
echo ""
echo "编辑cron任务:"
echo "  crontab -e"
echo ""
echo "删除cron任务:"
echo "  crontab -l | grep -v '$PYTHON_SCRIPT' | crontab -"
echo ""
echo "⚠️  请确保已正确配置环境变量文件: $ENV_FILE"
