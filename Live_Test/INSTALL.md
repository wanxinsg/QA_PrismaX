# 安装指南

## 快速安装

### 方式1: 使用脚本安装（推荐）

```bash
cd /Users/wanxin/PycharmProjects/Knowlege_PrismaX/QA_PrismaX/backend-test/Live_Framework
./run_tests.sh --install
```

### 方式2: 手动安装

```bash
cd /Users/wanxin/PycharmProjects/Knowlege_PrismaX/QA_PrismaX/backend-test/Live_Framework

# 使用 pip3 安装
pip3 install -r requirements.txt

# 或使用 python3 -m pip
python3 -m pip install -r requirements.txt
```

## 验证安装

```bash
# 检查 pytest 是否安装成功
python3 -m pytest --version

# 检查安装的包
pip3 list | grep pytest
pip3 list | grep allure
pip3 list | grep requests
```

## 可选：安装 Allure 报告工具

### macOS

```bash
brew install allure
```

### Linux

```bash
# 下载并安装
wget https://github.com/allure-framework/allure2/releases/download/2.13.8/allure-2.13.8.tgz
tar -zxvf allure-2.13.8.tgz
sudo mv allure-2.13.8 /opt/allure

# 添加到PATH
echo 'export PATH=$PATH:/opt/allure/bin' >> ~/.bashrc
source ~/.bashrc

# 验证安装
allure --version
```

## 运行第一个测试

```bash
# 运行简单的健康检查测试
python3 -m pytest test_cases/test_user_management.py::TestHealthCheck::test_health_check -v

# 或使用脚本
./run_tests.sh -t smoke
```

## 常见问题

### Q1: pip3 命令不存在

```bash
# 检查 Python 是否安装
python3 --version

# 如果 Python 已安装但 pip3 不存在，重新安装 pip
python3 -m ensurepip --default-pip

# 或下载安装
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py
```

### Q2: 权限问题

```bash
# 使用 --user 标志安装到用户目录
pip3 install --user -r requirements.txt
```

### Q3: 虚拟环境安装（推荐）

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# 或
.\venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 运行测试
pytest

# 退出虚拟环境
deactivate
```

## 依赖包说明

核心依赖：
- **pytest**: 测试框架
- **requests**: HTTP 请求库
- **allure-pytest**: 测试报告生成
- **python-dotenv**: 环境变量管理

可选依赖：
- **pytest-xdist**: 并行测试执行
- **pytest-timeout**: 测试超时控制
- **pytest-rerunfailures**: 失败重试

查看完整依赖列表：
```bash
cat requirements.txt
```

