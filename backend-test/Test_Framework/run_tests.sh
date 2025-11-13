#!/bin/bash

##############################################
# Knowlege_PrismaX Backend API 测试执行脚本
# 用途: 简化测试执行和报告生成
##############################################

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    cat << EOF
使用方法: ./run_tests.sh [选项]

选项:
    -h, --help              显示帮助信息
    -e, --env ENV           指定测试环境 (beta|live|local，默认: beta)
    -t, --type TYPE         测试类型 (smoke|regression|full，默认: regression)
    -s, --service SERVICE   测试服务 (user|tele|all，默认: all)
    -m, --marker MARKER     按pytest标记运行 (例如: smoke, critical)
    -r, --report            测试后生成并打开Allure报告
    -p, --parallel N        并行执行测试 (N为进程数，默认: 1)
    -c, --clean             清理旧的测试报告和日志
    --install               安装依赖
    --no-report             不生成Allure报告

示例:
    ./run_tests.sh                                  # 运行所有测试
    ./run_tests.sh -e beta -t smoke                 # 运行beta环境的冒烟测试
    ./run_tests.sh -s user -r                       # 只测试用户服务并生成报告
    ./run_tests.sh -m critical -p 4                 # 并行运行关键测试
    ./run_tests.sh --clean                          # 清理旧报告
    ./run_tests.sh --install                        # 安装依赖

EOF
}

# 默认参数
ENV="beta"
TEST_TYPE="regression"
SERVICE="all"
MARKER=""
GENERATE_REPORT=false
PARALLEL=1
CLEAN=false
INSTALL_DEPS=false
NO_REPORT=false

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -e|--env)
            ENV="$2"
            shift 2
            ;;
        -t|--type)
            TEST_TYPE="$2"
            shift 2
            ;;
        -s|--service)
            SERVICE="$2"
            shift 2
            ;;
        -m|--marker)
            MARKER="$2"
            shift 2
            ;;
        -r|--report)
            GENERATE_REPORT=true
            shift
            ;;
        -p|--parallel)
            PARALLEL="$2"
            shift 2
            ;;
        -c|--clean)
            CLEAN=true
            shift
            ;;
        --install)
            INSTALL_DEPS=true
            shift
            ;;
        --no-report)
            NO_REPORT=true
            shift
            ;;
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 检测 pip 命令
if command -v pip &> /dev/null; then
    PIP_CMD="pip"
elif command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
else
    print_error "未找到 pip 或 pip3 命令，请先安装 Python"
    exit 1
fi

# 安装依赖
if [ "$INSTALL_DEPS" = true ]; then
    print_info "安装测试依赖..."
    print_info "使用命令: $PIP_CMD"
    $PIP_CMD install -r requirements.txt
    print_success "依赖安装完成"
    exit 0
fi

# 清理旧报告
if [ "$CLEAN" = true ]; then
    print_info "清理旧的测试报告和日志..."
    rm -rf test_report/allure-results/*
    rm -rf test_report/allure-report/*
    rm -rf logs/*.log
    rm -rf .pytest_cache
    print_success "清理完成"
fi

# 创建必要的目录
mkdir -p test_report/allure-results
mkdir -p test_report/allure-report
mkdir -p logs

# 显示测试配置
print_info "==================== 测试配置 ===================="
print_info "测试环境: $ENV"
print_info "测试类型: $TEST_TYPE"
print_info "测试服务: $SERVICE"
[ -n "$MARKER" ] && print_info "测试标记: $MARKER"
print_info "并行进程: $PARALLEL"
print_info "生成报告: $GENERATE_REPORT"
print_info "=================================================="

# 设置环境变量
export TEST_ENV=$ENV

# 构建pytest命令
PYTEST_CMD="pytest"

# 添加测试文件参数
case $SERVICE in
    user)
        PYTEST_CMD="$PYTEST_CMD test_cases/test_user_management.py"
        ;;
    tele)
        PYTEST_CMD="$PYTEST_CMD test_cases/test_tele_op.py"
        ;;
    all)
        PYTEST_CMD="$PYTEST_CMD test_cases/"
        ;;
    *)
        print_error "无效的服务类型: $SERVICE"
        exit 1
        ;;
esac

# 添加标记参数
case $TEST_TYPE in
    smoke)
        PYTEST_CMD="$PYTEST_CMD -m smoke"
        ;;
    regression)
        # 回归测试运行除了slow之外的所有测试
        PYTEST_CMD="$PYTEST_CMD -m 'not slow'"
        ;;
    full)
        # 完整测试运行所有测试
        ;;
    *)
        print_error "无效的测试类型: $TEST_TYPE"
        exit 1
        ;;
esac

# 如果指定了自定义标记，覆盖测试类型的标记
if [ -n "$MARKER" ]; then
    PYTEST_CMD="pytest test_cases/ -m $MARKER"
fi

# 添加并行参数
if [ "$PARALLEL" -gt 1 ]; then
    PYTEST_CMD="$PYTEST_CMD -n $PARALLEL"
fi

# 添加环境参数
PYTEST_CMD="$PYTEST_CMD --env=$ENV"

# 执行测试
print_info "开始执行测试..."
print_info "命令: $PYTEST_CMD"
echo ""

# 记录开始时间
START_TIME=$(date +%s)

# 执行测试并捕获退出码
set +e
$PYTEST_CMD
TEST_EXIT_CODE=$?
set -e

# 记录结束时间
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
print_info "测试执行完成，耗时: ${DURATION}秒"

# 显示测试结果
if [ $TEST_EXIT_CODE -eq 0 ]; then
    print_success "所有测试通过！ ✅"
else
    print_warning "部分测试失败，退出码: $TEST_EXIT_CODE ⚠️"
fi

# 生成并打开Allure报告
if [ "$NO_REPORT" = false ]; then
    if command -v allure &> /dev/null; then
        print_info "生成Allure报告..."
        
        # 生成报告
        allure generate test_report/allure-results -o test_report/allure-report --clean
        
        print_success "Allure报告生成完成"
        print_info "报告位置: test_report/allure-report/index.html"
        
        # 如果指定了-r参数，打开报告
        if [ "$GENERATE_REPORT" = true ]; then
            print_info "打开Allure报告..."
            allure open test_report/allure-report
        fi
    else
        print_warning "未安装Allure命令行工具，跳过报告生成"
        print_info "安装方法: brew install allure (macOS) 或访问 https://docs.qameta.io/allure/"
    fi
fi

# 显示日志位置
echo ""
print_info "日志文件位置: logs/"
print_info "测试报告位置: test_report/"

# 退出
exit $TEST_EXIT_CODE

