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


### total_points 与 reward_points / point_transactions 的影响分析

- 定义：`total_points` 为 `users.total_points` 的持久化累计值，按事件发生“即时累加”。不是事后按 `point_transactions` 回放聚合得出。
- 一般规则：绝大多数积分发放同时做两件事
  - 写入 `users.total_points`（累加）
  - 写入 `point_transactions`（审计流水，含 `transaction_type`）
- 例外：邀请/返利读取时结算，仅更新 `users.total_points`，不写入 `point_transactions`（以 `users.referred_reward_point` 与 `users.referral_initial_reward` 记录已结算额度，防重复）。

#### 事件与写入的表
- 日常登录（Daily Login）
  - 表更新：`users`（`total_points += daily_points`），`point_transactions`（`transaction_type='daily_login'`，含 `user_local_date`）
- Tele‑Op 会话结算
  - 表更新：
    - `tele_op_control_history`（写入本次会话 `reward_points`、`controlled_end_time`、`controlled_hours`）
    - 如 `reward_points > 0`：`users`（`total_points += reward_points`），`point_transactions`（`transaction_type='first_time_tele_op' | 'robot_control_reward'`）
- 白皮书测验（Quiz）
  - 表更新：`users`（累加计算后的分值），`point_transactions`（`transaction_type='quiz'`）
- 有意义评论（每日一次）
  - 表更新：`users`（按会员等级累加），`point_transactions`（`transaction_type='comment_reward'`）
- 邀请/返利（读取即结算）
  - 表更新：仅 `users`（累加初始邀请 500×人数；返利差额 `floor(sum(referees.total_points)×10%) - referred_reward_point`），不写 `point_transactions`

#### 流程图（含表标注）

```mermaid
flowchart TD
  subgraph Tele-Op 会话结算
    A[开始会话\ntele_op_control_history] --> B{是否首次控制?}
    B -- 是 --> C[reward_points = 3000\n(首次奖励)]
    B -- 否 --> D{inactive?}
    D -- 是且<50s --> E[reward_points = 0]
    D -- 否/是且≥50s --> F[reward_points = floor((duration - (inactive?30s:0)) * 0.3)]

    C --> G[UPDATE tele_op_control_history\nSET reward_points, controlled_end_time, controlled_hours]
    E --> G
    F --> G

    G --> H{reward_points > 0?}
    H -- 否 --> I[结束]
    H -- 是 --> J[UPDATE users\nSET total_points = total_points + reward_points\n(users)]
    J --> K[INSERT point_transactions\n(points_change=reward_points,\n type=first_time_tele_op|robot_control_reward)]
    K --> I
  end

  subgraph Daily Login
    L[请求 /api/daily-login-points] --> M{当日是否已发?}
    M -- 否 --> N[计算 daily_points\n(Explorer 10, Amplifier 30, Innovator 50; Monad ×2)]
    N --> O[UPDATE users\nSET total_points += daily_points\n(users)]
    O --> P[INSERT point_transactions\n(points_change=daily_points,\n type=daily_login,\n user_local_date)]
    M -- 是 --> Q[跳过发放]
  end

  subgraph Quiz
    R[请求 /api/quiz/submit] --> S{是否已完成过?}
    S -- 否 --> T[计算 points: 500/题 + 全对额外 1000]
    T --> U[INSERT point_transactions\n(points_change=points,\n type=quiz)]
    U --> V[UPDATE users\nSET total_points += points\n(users)]
    S -- 是 --> W[拒绝重复领取]
  end

  subgraph 评论奖励
    X[请求 /api/check-comment-reward] --> Y{今天已领过?}
    Y -- 否 --> Z[计算 points: Explorer 50,\n非 Explorer 150]
    Z --> AA[UPDATE users\nSET total_points += points\n(users)]
    AA --> AB[INSERT point_transactions\n(points_change=points,\n type=comment_reward)]
    Y -- 是 --> AC[跳过发放]
  end

  subgraph 邀请/返利(读取结算)
    AD[请求 /api/get-users-by-referral] --> AE[校验 referrer]
    AE --> AF[计算初始邀请奖励: 500×referees_count]
    AF --> AG[UPDATE users\nSET total_points += invite_delta,\n referral_initial_reward = target\n(users)]
    AE --> AH[计算 10% 返利目标: floor(sum(referees.total_points)×10%)]
    AH --> AI[delta = target - referred_reward_point]
    AI --> AJ{delta > 0?}
    AJ -- 是 --> AK[UPDATE users\nSET total_points += delta,\n referred_reward_point = target\n(users)]
    AJ -- 否 --> AL[无变更]
    note right of AG: 不写入 point_transactions
    note right of AK: 不写入 point_transactions
  end
```

#### 重要说明
- `users.total_points` 为“事件驱动、逐次累加”的权威来源；前端展示 All‑Time 值时直接读取该字段。
- 事后修改 `tele_op_control_history.reward_points` 或随意增删 `point_transactions` 并不会自动回滚/同步 `users.total_points`。如需修正历史，需要相应更新 `users.total_points` 与对应审计流水，保证一致性。


#### 为什么“手动改会话积分不会自动影响总分”
- 一句话版：系统在“发放当时”就把积分累加进 `users.total_points` 并记一条流水。之后你去改历史记录表（例如 `tele_op_control_history.reward_points` 或某条 `point_transactions`），不会触发任何“回调”去重算 `users.total_points`；前端读取总分时也只看 `users.total_points`，不是汇总其他表。

- 原因：
  - All‑Time 展示接口直接读取 `users.total_points` 字段，而不是动态聚合 `point_transactions` 或 `tele_op_control_history`。
  - 发放流程是“事件驱动、即时累加”的设计，没有后台触发器或任务会在你修改历史记录后自动同步总分。

- 举例：
  - 某次会话原来算了 120 分，系统已经把 120 加到该用户的 `users.total_points`，并写入一条对应的 `point_transactions`。
  - 如果你事后把这次会话的 `reward_points` 改成 300：
    - `users.total_points` 不会自动多出 180；仍然停留在“+120”的状态。
    - 正确处理是另外把差额 `+180` 加到 `users.total_points`，同时补一条“纠正流水”（例如 `transaction_type='teleop_adjustment'`，`points_change=180`）用于审计。
  - 如果反向把 300 改回 120，也需要把差额 `-180` 同步减回并留痕。

- 正确修复步骤（建议）：
  1) 计算差额：`delta = newReward - oldReward`。
  2) 更新会话表：把 `tele_op_control_history.reward_points` 改为正确值（保持历史一致）。
  3) 同步总分：`UPDATE users SET total_points = total_points + :delta WHERE userid = :uid`。
  4) 审计留痕（其一）：
     - 新增一条纠正流水（推荐）：`point_transactions(points_change=delta, transaction_type='teleop_adjustment')`；
     - 或（不推荐）直接更新原始流水值，会弱化审计可追溯性。


#### 为什么“手动改会话积分不会自动影响总分”
- 一句话版：系统在“发放当时”就把积分累加进 `users.total_points` 并记一条流水。之后你去改历史记录表（例如 `tele_op_control_history.reward_points` 或某条 `point_transactions`），不会触发任何“回调”去重算 `users.total_points`；前端读取总分时也只看 `users.total_points`，不是汇总其他表。

- 原因：
  - All‑Time 展示接口直接读取 `users.total_points` 字段，而不是动态聚合 `point_transactions` 或 `tele_op_control_history`。
  - 发放流程是“事件驱动、即时累加”的设计，没有后台触发器或任务会在你修改历史记录后自动同步总分。

- 举例：
  - 某次会话原来算了 120 分，系统已经把 120 加到该用户的 `users.total_points`，并写入一条对应的 `point_transactions`。
  - 如果你事后把这次会话的 `reward_points` 改成 300：
    - `users.total_points` 不会自动多出 180；仍然停留在“+120”的状态。
    - 正确处理是另外把差额 `+180` 加到 `users.total_points`，同时补一条“纠正流水”（例如 `transaction_type='teleop_adjustment'`，`points_change=180`）用于审计。
  - 如果反向把 300 改回 120，也需要把差额 `-180` 同步减回并留痕。

- 正确修复步骤（建议）：
  1) 计算差额：`delta = newReward - oldReward`。
  2) 更新会话表：把 `tele_op_control_history.reward_points` 改为正确值（保持历史一致）。
  3) 同步总分：`UPDATE users SET total_points = total_points + :delta WHERE userid = :uid`。
  4) 审计留痕（其一）：
     - 新增一条纠正流水（推荐）：`point_transactions(points_change=delta, transaction_type='teleop_adjustment')`；
     - 或（不推荐）直接更新原始流水值，会弱化审计可追溯性。

