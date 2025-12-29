# Cloudflare Cache Purge E2E 手动测试用例

## 测试环境准备

### 前置条件
- [ ] Cloudflare Worker 已部署并绑定到目标路由
- [ ] 具有访问 Cloudflare Dashboard 的权限
- [ ] 准备测试用的 POST 请求工具（Postman/curl）
- [ ] 有权访问后端数据库查看数据变更
- [ ] 准备浏览器开发者工具用于检查网络请求
- [ ] 记录测试环境 URL：
  - Beta 环境：`beta-user.prismaxserver.com`
  - 生产环境：`user.prismaxserver.com`

### 测试数据准备
- [ ] 准备有效的 robot_id
- [ ] 准备有效的认证 token/session
- [ ] 记录 Cloudflare Zone ID：`404b821aad974edb640129f977823acd`

---

## 测试用例集

### TC-001: POST 请求成功 + 缓存清除成功（正常流程）

**测试目标**: 验证 POST 请求成功后，能正确触发 Cloudflare 缓存清除

**优先级**: P0 - 核心功能

**前置条件**:
1. Worker 脚本已正确部署
2. Cloudflare API Key 和 Email 配置正确
3. 目标 API 端点可正常访问

**测试步骤**:
1. 使用浏览器或 Postman 访问 `get_blockchain_config_address` 接口，确保数据被缓存
   ```bash
   curl -X GET "https://beta-user.prismaxserver.com/get_blockchain_config_address"
   ```
2. 记录缓存的响应数据（作为基准）
3. 发送 POST 请求更新 robot 的 live_paused 状态：
   ```bash
   curl -X POST "https://beta-user.prismaxserver.com/update_robot_status" \
     -H "Content-Type: application/json" \
     -d '{
       "robot_id": "test_robot_123",
       "live_paused": true
     }'
   ```
4. 检查 POST 请求的响应状态码
5. 检查响应头是否包含 `X-Cache-Purge-Triggered: true`
6. 立即再次访问 `get_blockchain_config_address` 接口
7. 在 Cloudflare Dashboard 中查看缓存清除日志

**预期结果**:
- [ ] POST 请求返回 2xx 状态码
- [ ] 响应头包含 `X-Cache-Purge-Triggered: true`
- [ ] 原始 API 响应数据保持不变（robot_id, live_paused 等字段正确）
- [ ] 再次访问 `get_blockchain_config_address` 时，返回最新数据（无缓存）
- [ ] Cloudflare 日志显示缓存清除成功

**实际结果**: 
```
测试日期: __________
测试人员: __________
结果: [ ] Pass  [ ] Fail
备注: 
```

---

### TC-002: POST 请求成功 + 缓存清除失败（错误处理）

**测试目标**: 验证当 POST 成功但缓存清除失败时，系统能正确处理并返回错误信息

**优先级**: P0 - 核心功能

**前置条件**:
1. 临时修改 Worker 中的 CF_API_KEY 为无效值，或
2. 临时修改 CF_ZONE_ID 为无效值

**测试步骤**:
1. 修改 Worker 配置，使 Cloudflare API 调用失败（修改 API Key）
2. 发送 POST 请求更新 robot 状态：
   ```bash
   curl -X POST "https://beta-user.prismaxserver.com/update_robot_status" \
     -H "Content-Type: application/json" \
     -d '{
       "robot_id": "test_robot_456",
       "live_paused": false
     }'
   ```
3. 检查响应状态码
4. 检查响应体的 JSON 结构
5. 检查响应头

**预期结果**:
- [ ] 响应状态码为 500
- [ ] 响应头包含 `X-Cache-Purge-Error: true`
- [ ] 响应体包含以下字段：
  ```json
  {
    "success": false,
    "msg": "Error resetting the Cloudflare CloudFlare_Cache. Manually clear the Cloudflare CloudFlare_Cache to avoid inconsistencies now. Live paused status has been updated in the database.",
    "robot_id": "test_robot_456",
    "live_paused": false
  }
  ```
- [ ] 数据库中的 live_paused 状态已更新（需查询数据库验证）
- [ ] 缓存未被清除（仍然返回旧数据）

**实际结果**: 
```
测试日期: __________
测试人员: __________
结果: [ ] Pass  [ ] Fail
备注: 
```

---

### TC-003: POST 请求失败（不触发缓存清除）

**测试目标**: 验证 POST 请求失败时，不会触发缓存清除操作

**优先级**: P1 - 重要功能

**前置条件**:
1. Worker 脚本已正确部署
2. 准备会导致 POST 失败的请求参数

**测试步骤**:
1. 先访问 `get_blockchain_config_address` 确保有缓存数据
2. 发送会导致失败的 POST 请求（例如：缺少必需参数、认证失败等）：
   ```bash
   # 缺少必需参数
   curl -X POST "https://beta-user.prismaxserver.com/update_robot_status" \
     -H "Content-Type: application/json" \
     -d '{}'
   ```
3. 检查响应状态码（应为 4xx 或 5xx）
4. 检查响应头是否包含 `X-Cache-Purge-Triggered`
5. 再次访问 `get_blockchain_config_address` 检查缓存状态
6. 查看 Cloudflare 缓存清除日志

**预期结果**:
- [ ] POST 请求返回 4xx 或 5xx 状态码（非 2xx）
- [ ] 响应头**不包含** `X-Cache-Purge-Triggered`
- [ ] 响应头**不包含** `X-Cache-Purge-Error`
- [ ] 缓存保持不变（访问 `get_blockchain_config_address` 仍返回缓存数据）
- [ ] Cloudflare 日志中无缓存清除记录

**实际结果**: 
```
测试日期: __________
测试人员: __________
结果: [ ] Pass  [ ] Fail
备注: 
```

---

### TC-004: 验证缓存清除的 URL 前缀正确性

**测试目标**: 确认只清除指定前缀的缓存，不影响其他缓存

**优先级**: P1 - 重要功能

**前置条件**:
1. Worker 脚本已正确部署
2. 有多个不同的 API 端点已缓存

**测试步骤**:
1. 访问以下端点并确保都已缓存：
   - `https://beta-user.prismaxserver.com/get_blockchain_config_address`
   - `https://user.prismaxserver.com/get_blockchain_config_address`
   - `https://beta-user.prismaxserver.com/other_api_endpoint`（其他端点）
2. 记录每个端点的缓存响应数据
3. 发送成功的 POST 请求触发缓存清除
4. 立即访问上述所有端点
5. 比对数据是否从缓存返回

**预期结果**:
- [ ] `beta-user.prismaxserver.com/get_blockchain_config_address` 缓存已清除
- [ ] `user.prismaxserver.com/get_blockchain_config_address` 缓存已清除
- [ ] 其他不在前缀列表中的端点缓存**未被清除**（仍返回缓存数据）
- [ ] Cloudflare Dashboard 显示只清除了指定前缀的缓存

**实际结果**: 
```
测试日期: __________
测试人员: __________
结果: [ ] Pass  [ ] Fail
备注: 
```

---

### TC-005: 并发请求场景测试

**测试目标**: 验证多个并发 POST 请求时，缓存清除操作的正确性

**优先级**: P2 - 一般功能

**前置条件**:
1. Worker 脚本已正确部署
2. 准备并发测试工具（Apache Bench、JMeter 或脚本）

**测试步骤**:
1. 确保目标接口有缓存数据
2. 同时发送 5 个 POST 请求：
   ```bash
   # 可使用以下脚本
   for i in {1..5}; do
     curl -X POST "https://beta-user.prismaxserver.com/update_robot_status" \
       -H "Content-Type: application/json" \
       -d "{\"robot_id\": \"robot_$i\", \"live_paused\": true}" &
   done
   wait
   ```
3. 检查所有响应
4. 查看 Cloudflare 缓存清除日志
5. 验证缓存是否被正确清除

**预期结果**:
- [ ] 所有 5 个请求都返回成功（2xx）
- [ ] 每个响应都包含 `X-Cache-Purge-Triggered: true`
- [ ] 缓存被成功清除（可能触发多次清除操作，但不影响结果）
- [ ] 没有出现竞态条件或错误
- [ ] 系统性能稳定，响应时间在可接受范围

**实际结果**: 
```
测试日期: __________
测试人员: __________
结果: [ ] Pass  [ ] Fail
备注: 
```

---

### TC-006: 大型响应体处理测试

**测试目标**: 验证处理大型响应体时的正确性

**优先级**: P2 - 一般功能

**前置条件**:
1. Worker 脚本已正确部署
2. 准备会返回大型响应的 POST 请求

**测试步骤**:
1. 发送 POST 请求，预期返回较大的响应体（>1MB）
2. 观察 Worker 处理时间
3. 检查响应是否完整
4. 验证缓存清除是否仍然触发

**预期结果**:
- [ ] 大型响应体被完整返回
- [ ] 响应头正确添加 `X-Cache-Purge-Triggered: true`
- [ ] 缓存清除成功执行
- [ ] Worker 没有超时或内存错误

**实际结果**: 
```
测试日期: __________
测试人员: __________
结果: [ ] Pass  [ ] Fail
备注: 
```

---

### TC-007: 网络超时场景测试

**测试目标**: 验证 Cloudflare API 调用超时时的处理

**优先级**: P2 - 一般功能

**前置条件**:
1. 能够模拟网络延迟或超时（可通过修改 Worker 代码添加长延迟）

**测试步骤**:
1. 模拟 Cloudflare API 响应超时场景
2. 发送 POST 请求
3. 观察 Worker 行为
4. 检查响应状态和错误处理

**预期结果**:
- [ ] Worker 能捕获超时异常
- [ ] 返回 500 错误码和相应错误消息
- [ ] 响应头包含 `X-Cache-Purge-Error: true`
- [ ] 用户收到明确的错误提示

**实际结果**: 
```
测试日期: __________
测试人员: __________
结果: [ ] Pass  [ ] Fail
备注: 
```

---

### TC-008: 响应头完整性验证

**测试目标**: 验证 Worker 正确保留和修改响应头

**优先级**: P2 - 一般功能

**前置条件**:
1. Worker 脚本已正确部署
2. 准备检查响应头的工具

**测试步骤**:
1. 发送成功的 POST 请求
2. 使用 curl -v 或浏览器开发者工具检查完整的响应头：
   ```bash
   curl -v -X POST "https://beta-user.prismaxserver.com/update_robot_status" \
     -H "Content-Type: application/json" \
     -d '{"robot_id": "test", "live_paused": true}'
   ```
3. 验证所有原始响应头是否保留
4. 验证新增的自定义响应头

**预期结果**:
- [ ] 所有原始响应头被保留（Content-Type, Content-Length 等）
- [ ] 新增 `X-Cache-Purge-Triggered: true` 响应头
- [ ] 响应头格式正确，无重复或冲突

**实际结果**: 
```
测试日期: __________
测试人员: __________
结果: [ ] Pass  [ ] Fail
备注: 
```

---

### TC-009: JSON 格式错误响应验证

**测试目标**: 验证当原始响应不是有效 JSON 时的处理

**优先级**: P3 - 次要功能

**前置条件**:
1. 能够让后端返回非 JSON 格式的响应

**测试步骤**:
1. 配置后端返回纯文本或 HTML 响应
2. 发送 POST 请求
3. 观察 Worker 行为
4. 检查是否有 JavaScript 错误

**预期结果**:
- [ ] Worker 能处理非 JSON 响应而不崩溃
- [ ] 或者在解析失败时返回适当的错误
- [ ] 不影响正常的请求转发功能

**实际结果**: 
```
测试日期: __________
测试人员: __________
结果: [ ] Pass  [ ] Fail
备注: 
```

---

### TC-010: 跨环境验证（Beta vs Production）

**测试目标**: 确认两个环境的缓存清除都能正常工作

**优先级**: P0 - 核心功能

**前置条件**:
1. Beta 和 Production 环境都已部署 Worker
2. 两个环境都有测试数据

**测试步骤**:
1. 在 Beta 环境执行 TC-001
2. 在 Production 环境执行 TC-001
3. 验证两个环境的缓存清除前缀配置
4. 确认两个环境都能正确清除缓存

**预期结果**:
- [ ] Beta 环境：清除 `beta-user.prismaxserver.com/get_blockchain_config_address`
- [ ] Production 环境：清除 `user.prismaxserver.com/get_blockchain_config_address`
- [ ] 两个环境的缓存清除都能成功
- [ ] 不存在跨环境影响（Beta 操作不影响 Production 缓存）

**实际结果**: 
```
测试日期: __________
测试人员: __________
结果: [ ] Pass  [ ] Fail
备注: 
```

---

## 性能测试

### PT-001: 缓存清除响应时间

**测试目标**: 测量缓存清除操作对响应时间的影响

**测试步骤**:
1. 测量不使用 Worker 时的 POST 请求响应时间（基准）
2. 测量使用 Worker 且缓存清除成功时的响应时间
3. 计算增加的延迟
4. 重复测试 20 次取平均值

**预期结果**:
- [ ] 响应时间增加 < 500ms
- [ ] 99% 的请求在 2 秒内完成

**实际结果**: 
```
基准响应时间（平均）: _______ ms
Worker 响应时间（平均）: _______ ms
增加的延迟: _______ ms
```

---

## 安全测试

### ST-001: API Key 泄露风险验证

**测试目标**: 确认 API Key 不会在响应中泄露

**优先级**: P0 - 安全关键

**测试步骤**:
1. 发送各种 POST 请求（成功和失败场景）
2. 检查所有响应体和响应头
3. 检查浏览器开发者工具的网络面板
4. 检查 Cloudflare 日志

**预期结果**:
- [ ] 响应中不包含 CF_API_KEY
- [ ] 响应中不包含 CF_AUTH_EMAIL（可见但应脱敏）
- [ ] 错误消息不泄露敏感信息

**实际结果**: 
```
测试日期: __________
测试人员: __________
结果: [ ] Pass  [ ] Fail
备注: 
```

---

## 测试数据记录模板

### 测试执行摘要

| 测试用例 | 优先级 | 状态 | 执行时间 | 测试人员 | 备注 |
|---------|--------|------|----------|---------|------|
| TC-001  | P0     |      |          |         |      |
| TC-002  | P0     |      |          |         |      |
| TC-003  | P1     |      |          |         |      |
| TC-004  | P1     |      |          |         |      |
| TC-005  | P2     |      |          |         |      |
| TC-006  | P2     |      |          |         |      |
| TC-007  | P2     |      |          |         |      |
| TC-008  | P2     |      |          |         |      |
| TC-009  | P3     |      |          |         |      |
| TC-010  | P0     |      |          |         |      |
| PT-001  | P1     |      |          |         |      |
| ST-001  | P0     |      |          |         |      |

### Bug 记录模板

```
Bug ID: BUG-XXX
严重程度: [ ] Critical [ ] High [ ] Medium [ ] Low
关联用例: TC-XXX
复现步骤:
1. 
2. 
3. 

预期结果:

实际结果:

环境信息:
- Worker 版本: 
- 测试环境: 
- 测试时间: 

附件:
- 截图: 
- 日志: 
```

---

## 测试工具和命令

### 1. 基本 curl 命令模板

```bash
# GET 请求检查缓存
curl -v -X GET "https://beta-user.prismaxserver.com/get_blockchain_config_address" \
  -H "Authorization: Bearer YOUR_TOKEN"

# POST 请求触发缓存清除
curl -v -X POST "https://beta-user.prismaxserver.com/update_robot_status" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "robot_id": "test_robot_123",
    "live_paused": true
  }'

# 查看完整响应头
curl -I -X POST "https://beta-user.prismaxserver.com/update_robot_status" \
  -H "Content-Type: application/json" \
  -d '{"robot_id": "test", "live_paused": true}'
```

### 2. 检查 Cloudflare 缓存状态

```bash
# 使用 curl 查看缓存状态（检查 CF-Cache-Status 响应头）
curl -v "https://beta-user.prismaxserver.com/get_blockchain_config_address" 2>&1 | grep -i "cf-cache"
```

### 3. 并发测试脚本

```bash
#!/bin/bash
# concurrent_test.sh

URL="https://beta-user.prismaxserver.com/update_robot_status"
CONCURRENT=5

for i in $(seq 1 $CONCURRENT); do
  (
    response=$(curl -s -w "\n%{http_code}" -X POST "$URL" \
      -H "Content-Type: application/json" \
      -d "{\"robot_id\": \"robot_$i\", \"live_paused\": true}")
    echo "Request $i: $response"
  ) &
done

wait
echo "All requests completed"
```

---

## 注意事项

1. **测试前备份**: 在执行测试前，确保有数据备份
2. **避免生产环境**: 优先在 Beta 环境完成所有测试
3. **监控告警**: 测试期间监控是否触发任何告警
4. **日志收集**: 保存所有测试的请求/响应日志
5. **回滚计划**: 准备 Worker 的回滚方案
6. **清理测试数据**: 测试完成后清理所有测试数据

---

## 已知限制和风险

1. **API Key 硬编码**: 当前 API Key 直接写在代码中，存在安全风险
2. **单点故障**: 如果 Cloudflare API 不可用，会影响业务流程
3. **缓存清除延迟**: 缓存清除可能需要一定时间才能在全球生效
4. **响应体修改**: 在错误情况下修改了原始响应体，可能影响客户端解析

---

## 测试完成检查清单

- [ ] 所有 P0 用例已执行并通过
- [ ] 所有 P1 用例已执行
- [ ] 所有发现的 Bug 已记录
- [ ] 性能测试已完成
- [ ] 安全测试已完成
- [ ] 测试报告已编写
- [ ] 测试数据已清理
- [ ] 相关文档已更新

