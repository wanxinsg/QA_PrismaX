### 前端逻辑

- 数据来源：`GET /api/get-point-transactions`（同上接口返回的数据）。
- 前端计算逻辑（发生在首页 Dashboard）：
  1. 在用户本地时区生成“今天”的日期字符串：`YYYY-MM-DD`。
  2. 遍历接口返回的 `data`（近 14 天内的积分变动），对每条记录确定其“记账日”：
     - 若存在 `user_local_date`，直接解析为 `YYYY-MM-DD` 使用；
     - 否则使用 `created_at_utc` 将 UTC 时间转换为本地时间，再取 `YYYY-MM-DD`。
  3. 仅保留“记账日 == 今天”且 `points_change > 0` 的记录。
  4. 对上述记录的 `points_change` 求和（向下取整）后显示为“Daily Prisma Points”。

- 相关字段：
  - `points_change`: 本次变动的积分，正数为增加；
  - `user_local_date`: 后端记录的用户本地日期（若有则优先）；
  - `created_at_utc`: 变动发生的 UTC 时间戳（用于本地化日期的后备）。

-
- All‑Time Prisma Points：直接使用接口返回的 `total_points`。
- Earnings 折线图：使用近 14 天 `point_transactions`，前端按天聚合 `points_change > 0` 之和。



### API — GET /api/get-point-transactions

**作用**  
按用户（通过 `email` 或 `wallet_address`）查询近 14 天的积分变动记录，并在用户维度查询时附带返回当前 `total_points`。

### 入参
- **email**（可选，和 `wallet_address` 二选一）：用于按邮箱定位用户（会转为小写）
- **wallet_address**（可选，和 `email` 二选一）：用于按链上地址定位用户
- **chain**（可选，默认 `solana`）：仅在使用 `wallet_address` 查询时用于选择 `users` 表中对应链地址列；支持：`solana | ethereum | base | monad | aptos`

### 时间窗口
- 固定查询最近 14 天：`created_at_utc >= (UTC现在 - 14天)`，按 `created_at_utc` 倒序返回。

### 读取的数据表
- **users**
  - 用途：通过 `email` 或（当有 `wallet_address` 时）通过链映射列 `CHAIN_COLUMN_MAP[chain]` 定位到 `userid`；同时读取 `total_points`。
  - 关键读取字段：`userid`, `total_points`，以及用于匹配的 `email` 或链上地址列（如 `solana_address` 等）。
- **point_transactions**
  - 用途：按 `userid` 和 14 天窗口提取积分变动记录。
  - 典型字段（根据实际表结构可能包含）：`transaction_id`, `userid`, `points_change`, `transaction_type`, `user_local_date`, `created_at_utc` 等。

### 返回
- 当使用 `email` 或 `wallet_address` 成功定位到用户时：
  - `success: true`
  - `data: [ ...point_transactions 记录... ]`
  - `total_points: <users.total_points>`
- 当未带用户标识（`email`/`wallet_address` 都无）时：
  - 返回近 14 天的全量 `point_transactions`（不附带 `total_points`）。


### point_transactions 的更新来源与写入规则

- 日常登录（Daily Login）
  - 接口：`POST /api/daily-login-points`
  - 动作：按会员等级与链（Monad ×2）计算当日登录积分，更新 `users.total_points`，并插入 `point_transactions`：
    - `transaction_type='daily_login'`
    - 写入 `user_local_date=YYYY-MM-DD`（用于前端本地日聚合）
  - 防重：按 `userid + user_local_date` 当日只发一次。

- Tele‑Op 会话结束结算
  - 位置：控制服务的奖励结算（`process_session_rewards`）
  - 规则：
    - 首次控制奖励固定 3000 分（`transaction_type='first_time_tele_op'`）
    - 之后以约 `0.3 分/秒` 结算（非活跃减 30 秒），`transaction_type='robot_control_reward'`
  - 动作：更新 `users.total_points`；插入 `point_transactions`，时间使用 `created_at_utc=NOW() AT TIME ZONE 'UTC'`。

- 白皮书测验（Quiz）
  - 接口：`POST /api/quiz/submit`
  - 动作：人机验证通过后计算总分；若已完成过则拒绝；否则插入 `point_transactions (transaction_type='quiz')` 并更新 `users.total_points`。

- 有意义评论奖励（每日一次）
  - 接口：`POST /api/check-comment-reward`
  - 动作：用 `DATE(created_at_utc)=UTC今日` 防重复；发放积分并插入 `point_transactions (transaction_type='comment_reward')`。

- 邀请/返利（读取时结算，避免过多流水）
  - 接口：`GET /api/get-users-by-referral`
  - 动作：读取时为邀请人结算初始邀请奖励（每个被邀请用户 500 分）与 10% 返利，直接累加到 `users.total_points`；不写入 `point_transactions`。


