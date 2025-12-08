#!/bin/bash

##############################################
# 快速激活虚拟环境脚本
# 用途: 简化虚拟环境激活操作
##############################################

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Prismax 测试框架 - 虚拟环境激活${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# 检查虚拟环境是否存在
if [ ! -d "testenv" ]; then
    echo -e "${RED}❌ 错误: testenv 虚拟环境不存在${NC}"
    echo "请先创建虚拟环境："
    echo "  python3 -m venv testenv"
    echo "  source testenv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# 激活虚拟环境
echo -e "${GREEN}✅ 激活虚拟环境...${NC}"
source testenv/bin/activate

# 显示环境信息
echo ""
echo -e "${GREEN}📦 虚拟环境信息:${NC}"
echo "  Python: $(which python)"
echo "  版本: $(python --version)"
echo "  pytest: $(pytest --version 2>&1 | head -n 1)"
echo ""

echo -e "${GREEN}🚀 使用提示:${NC}"
echo "  • 运行测试: pytest -v"
echo "  • 运行脚本: ./run_tests.sh"
echo "  • 查看帮助: pytest --help"
echo "  • 退出环境: deactivate"
echo ""

echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}✅ 虚拟环境已激活！开始测试吧！${NC}"
echo -e "${BLUE}================================================${NC}"

# 启动一个新的shell会话，保持虚拟环境激活
exec $SHELL

