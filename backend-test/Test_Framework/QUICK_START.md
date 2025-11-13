# 快速开始指南

## 🚀 运行测试的几种方式

### 方式1: 使用便捷脚本（推荐）

```bash
# 进入测试框架目录
cd /Users/wanxin/PycharmProjects/Knowlege_PrismaX/QA_PrismaX/backend-test/Test_Framework

# 1. 首次使用：安装依赖
./run_tests.sh --install

# 2. 运行所有测试（默认beta环境）
./run_tests.sh

# 3. 运行冒烟测试
./run_tests.sh -t smoke

# 4. 只测试用户管理服务
./run_tests.sh -s user

# 5. 只测试机器人控制服务
./run_tests.sh -s tele

# 6. 运行测试并生成报告
./run_tests.sh -r

# 7. 并行运行测试（4个进程）
./run_tests.sh -p 4

# 8. 清理旧报告后运行
./run_tests.sh --clean -r

# 9. 查看所有选项
./run_tests.sh --help
```

### 方式2: 直接使用 pytest 命令

```bash
# 进入测试框架目录
cd /Users/wanxin/PycharmProjects/Knowlege_PrismaX/QA_PrismaX/backend-test/Test_Framework

# 1. 运行所有测试
pytest

# 2. 运行指定文件
pytest test_cases/test_user_management.py
pytest test_cases/test_tele_op.py

# 3. 运行指定测试类
pytest test_cases/test_user_management.py::TestHealthCheck

# 4. 运行指定测试方法
pytest test_cases/test_user_management.py::TestHealthCheck::test_health_check

# 5. 按标记运行
pytest -m smoke          # 运行冒烟测试
pytest -m critical       # 运行关键测试
pytest -m "not slow"     # 跳过慢速测试

# 6. 指定环境
pytest --env=beta
pytest --env=live
pytest --env=local

# 7. 并行运行（需要先安装 pytest-xdist）
pytest -n auto           # 自动检测CPU核心数
pytest -n 4              # 使用4个进程

# 8. 显示详细输出
pytest -v -s

# 9. 只运行失败的测试
pytest --lf              # last failed
pytest --ff              # failed first
```

## 📊 查看测试报告

### 方式1: 使用脚本生成报告

```bash
# 运行测试并自动打开Allure报告
./run_tests.sh -r

# 或者手动生成报告
allure serve test_report/allure-results
```

### 方式2: 手动生成Allure报告

```bash
# 1. 运行测试（会自动生成 allure-results）
pytest

# 2. 生成HTML报告
allure generate test_report/allure-results -o test_report/allure-report --clean

# 3. 打开报告
allure open test_report/allure-report

# 或者一步到位：
allure serve test_report/allure-results
```

### 方式3: 查看日志文件

```bash
# 查看最新的测试日志
cat logs/test_$(date +%Y%m%d).log

# 查看 pytest 日志
cat logs/pytest.log

# 实时查看日志
tail -f logs/test_$(date +%Y%m%d).log
```

## 🔧 常用测试场景

### 场景1: 快速验证功能（冒烟测试）

```bash
# 只运行关键的健康检查和基础功能
./run_tests.sh -t smoke -r

# 或
pytest -m smoke -v
```

### 场景2: 开发过程中的回归测试

```bash
# 运行除慢速测试外的所有测试
./run_tests.sh -t regression -p 4

# 或
pytest -m "not slow" -n 4
```

### 场景3: 发布前的完整测试

```bash
# 运行所有测试，包括慢速测试，生成详细报告
./run_tests.sh -t full -r

# 或
pytest -v --durations=10
allure serve test_report/allure-results
```

### 场景4: 只测试新功能

```bash
# 运行特定的测试类或方法
pytest test_cases/test_user_management.py::TestPaymentSystem -v
```

### 场景5: 调试失败的测试

```bash
# 详细输出 + 显示print + 进入调试模式
pytest test_cases/test_user_management.py::TestHealthCheck::test_health_check -v -s --pdb

# 或只运行上次失败的测试
pytest --lf -v -s
```

## 🌍 切换测试环境

### 使用脚本指定环境

```bash
# Beta环境（默认）
./run_tests.sh -e beta

# Live生产环境
./run_tests.sh -e live

# 本地环境
./run_tests.sh -e local
```

### 使用环境变量

```bash
# 设置环境变量
export TEST_ENV=beta

# 运行测试
pytest
```

### 临时指定环境

```bash
# 只在本次运行时使用指定环境
TEST_ENV=local pytest
```

## 📝 查看可用的测试标记

```bash
# 列出所有可用的标记
pytest --markers

# 常用标记：
# - smoke: 冒烟测试
# - critical: 关键功能
# - high: 高优先级
# - medium: 中优先级
# - low: 低优先级
# - slow: 慢速测试
# - integration: 集成测试
```

## 🐛 调试技巧

### 1. 查看详细的HTTP请求日志

```bash
# 运行测试时显示所有print输出
pytest -s

# 查看日志文件中的详细HTTP请求
cat logs/test_$(date +%Y%m%d).log | grep "Request:"
```

### 2. 进入Python调试器

```bash
# 遇到失败时自动进入pdb
pytest --pdb

# 或在测试代码中添加断点
import pdb; pdb.set_trace()
```

### 3. 只运行特定的测试

```bash
# 使用 -k 参数匹配测试名称
pytest -k "health"           # 运行所有包含"health"的测试
pytest -k "test_health or test_status"  # 运行多个
```

### 4. 查看测试执行时间

```bash
# 显示最慢的10个测试
pytest --durations=10

# 显示所有测试的执行时间
pytest --durations=0
```

## ⚙️ 完整的工作流程示例

### 第一次使用

```bash
# 1. 进入目录
cd /Users/wanxin/PycharmProjects/Knowlege_PrismaX/QA_PrismaX/backend-test/Test_Framework

# 2. 安装依赖
./run_tests.sh --install

# 3. 运行冒烟测试验证环境
./run_tests.sh -t smoke -r

# 4. 如果冒烟测试通过，运行完整测试
./run_tests.sh -t full -r
```

### 日常开发测试

```bash
# 1. 清理旧报告
./run_tests.sh --clean

# 2. 运行回归测试
./run_tests.sh -t regression -p 4

# 3. 如果有失败，运行失败的测试查看详情
pytest --lf -v -s

# 4. 修复后重新运行
pytest --lf
```

### 发布前验证

```bash
# 1. 在beta环境运行完整测试
./run_tests.sh -e beta -t full -r

# 2. 查看报告，确认所有测试通过

# 3. 在live环境运行冒烟测试
./run_tests.sh -e live -t smoke -r

# 4. 确认无误后发布
```

## 📋 常见问题

### Q1: 如何安装 Allure？

```bash
# macOS
brew install allure

# Linux
wget https://github.com/allure-framework/allure2/releases/download/2.13.8/allure-2.13.8.tgz
tar -zxvf allure-2.13.8.tgz
sudo mv allure-2.13.8 /opt/allure
echo 'export PATH=$PATH:/opt/allure/bin' >> ~/.bashrc
source ~/.bashrc
```

### Q2: 测试失败如何查看详细信息？

```bash
# 方法1: 查看Allure报告
allure serve test_report/allure-results

# 方法2: 查看日志文件
cat logs/test_$(date +%Y%m%d).log

# 方法3: 重新运行失败的测试并显示详细输出
pytest --lf -v -s
```

### Q3: 如何跳过某些测试？

```bash
# 在测试代码中添加装饰器
@pytest.mark.skip(reason="原因说明")
def test_example():
    pass

# 或运行时跳过
pytest -m "not slow"  # 跳过慢速测试
```

### Q4: 如何更新服务URL？

```bash
# 方法1: 修改 config.py 文件

# 方法2: 使用环境变量
export BETA_USER_MANAGEMENT_URL=https://new-url.com
export BETA_TELE_OP_URL=https://new-url.com

# 方法3: 创建 .env 文件
echo "BETA_USER_MANAGEMENT_URL=https://new-url.com" > .env
echo "BETA_TELE_OP_URL=https://new-url.com" >> .env
```

## 🎯 推荐的测试策略

1. **每次提交前**: 运行冒烟测试 `./run_tests.sh -t smoke`
2. **每天**: 运行回归测试 `./run_tests.sh -t regression -r`
3. **发布前**: 运行完整测试 `./run_tests.sh -t full -r`
4. **CI/CD**: 配置自动化测试流水线

---

**提示**: 如果您是第一次运行，建议先运行 `./run_tests.sh --help` 查看所有可用选项！

