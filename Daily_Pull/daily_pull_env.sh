#!/bin/bash
#
# Daily Pull 环境变量配置文件
# 用于cron任务中设置环境变量
#
# 使用方法:
#   source /Users/wanxin/PycharmProjects/Prismax/QA_PrismaX/Daily_Pull/daily_pull_env.sh
#

# SMTP服务器配置
export SMTP_HOST="${SMTP_HOST:-mail.privateemail.com}"
export SMTP_PORT="${SMTP_PORT:-465}"
export SMTP_SECURITY="${SMTP_SECURITY:-ssl}"

# SMTP认证信息（请根据实际情况修改）
export SMTP_USER="${SMTP_USER:-your_email@example.com}"
export SMTP_PASS="${SMTP_PASS:-your_password}"

# 邮件发送配置
export EMAIL_FROM="${EMAIL_FROM:-${SMTP_USER}}"
export EMAIL_TO="${EMAIL_TO:-wanxin@solidcap.io}"
export EMAIL_SUBJECT="${EMAIL_SUBJECT:-Prismax Daily Testing Branches Pull Report}"

# 项目根目录（可选，默认自动检测）
# export PROJECT_ROOT="/Users/wanxin/PycharmProjects/Prismax"
