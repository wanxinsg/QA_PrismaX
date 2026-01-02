## Prismax 用户管理系统业务逻辑说明（app_prismax_user_management）

本文基于 `app_prismax_user_management/app.py` 及相关辅助模块，总结 Prismax 用户管理（user_management）的核心业务逻辑，供需求、测试与排查参考。

---

## 一、整体概览

- **身份标识与登录方式并存**
  - 支持 **邮箱验证码登录**（无固定密码）、第三方登录（Google/Apple，经 `login_type` 区分）、以及 **多链钱包登录**（Solana/Ethereum/Base/Monad/Aptos）。
  - 系统统一使用 `users.hash_code` 作为“长效登录令牌”（token），前端通常通过 `Authorization: Bearer <hash_code>` 传回认证。

- **多角色 / 会员等级体系**
  - `users.user_class` 字段定义会员等级：
    - `Explorer Member`：默认免费用户。
    - `Amplifier Member`：99 美金付费升级。
    - `Innovator Member`：399 美金进一步升级。
  - 部分**高级功能**仅对特定会员等级开放，典型包括：
    - **TeleOp 机器人远程控制**：
      - Explorer：完全禁止使用所有 TeleOp 机器人（加入任意 `arm1/arm2/arm3` 队列都会返回 403）。
      - Amplifier：
        - Training Arm（`arm1`）：每个 UTC 自然日最多成功入队 **3 次**（基于 `robot_queue.created_at` 统计），第 4 次及之后会返回 403。
        - Buddy Arm（`arm3`）：终身总共最多 **3 次** TeleOp 使用（依据 `tele_op_control_history.robot_id='arm3'` 统计）。
        - Monad Arm（`arm2`）：当前版本在会员维度**无额外次数上限**，仅受通用队列 / Fast Track 规则约束。
        - Amplifier 无机器人预约权限。
      - Innovator：可使用所有 TeleOp 功能（含 Fast Track 抢占队列和全部三种机械臂），并享有更高积分倍率。
    - **机器人预约 `/api/reserve-robot`**：
      - 仅对 Innovator Member 开放，用于预约线下演示或远程 TeleOp 体验（需 `user_id + token` 校验）。
    - **Fast Track（TeleOp 队列抢占）**：
      - 仅 Innovator 可使用，且所有机器人合计每天最多 6 次 Fast Track 机会（跨 `arm1/arm2/arm3` 共享）。

- **多链钱包 + 邮箱双渠道账户体系**
  - 用户既可以从 **邮箱** 进入，也可以从 **钱包地址** 进入。
  - 通过 `linked_email`、`linked_wallet_address` 将“邮箱账户”和“钱包账户”建立绑定关系，统一视为同一用户身份。

- **积分与权益体系深度绑定**
  - 积分累积方式：首次登录奖励、每日登录、测验问卷、评论奖励、推荐关系分成等，均通过 `point_transactions` + `users.total_points` 管理。
  - 会员等级与积分奖励倍率挂钩（例如 Innovator 日常积分更高）。

- **支付与会员升级闭环**
  - Stripe 支付（信用卡）与多链加密支付（Solana/EVM/Base/Monad/Aptos）均记录在 `purchase_records` 中。
  - 支付金额满足条件时，自动将用户会员等级从 `Explorer → Amplifier → Innovator` 升级。

- **外部服务绑定**
  - Twitter OAuth：绑定到用户记录的 `user_profile_twitter_id`、`user_profile_twitter_name`。
  - YouTube 仅作为监控/告警使用，不直接影响用户身份，但和 `robot_status`、系统管理员通知相关。

---

## 二、核心数据结构（表与关键字段）

> 以下字段来自于 SQL 查询与更新逻辑推断，实际 DDL 以数据库为准。

### 1. `users` 表（用户主表）

**身份与登录相关**
- `userid`：主键，自增。
- `email`：登录邮箱（可为空，用于邮箱体系）。
- `login_type`：登录类型，`'0'` 表示邮箱验证码登录，其他值用于 Google/Apple 等第三方。
- `hash_code`：当前登录 token，相当于“会话/长期登录令牌”，每次成功登录或登出都会刷新。

**钱包与链上地址（多链）**
- `solana_receive_address`
- `ethereum_receive_address`
- `base_receive_address`
- `monad_receive_address`
- `aptos_receive_address`

**邮箱与钱包绑定关系**
- `linked_email`：钱包用户绑定的邮箱。
- `linked_wallet_address`：邮箱用户绑定的钱包地址（具体链通过运行时逻辑推断）。

**会员与积分体系**
- `user_class`：会员等级（`Explorer Member` / `Amplifier Member` / `Innovator Member`）。
- `total_points`：当前可用积分总数。
- `referral_code`：该用户对外分享的推荐码。
- `referrers_referral_code`：该用户注册时填写的推荐人推荐码（即“我是谁拉来的”）。
- `referred_reward_point`：推荐 10% 分成已结算积分（防止重复结算）。
- `referral_initial_reward`：初始邀请奖励（每个被邀请人 500 积分）已发放总额。

**个人资料 / 联系方式**
- `user_name`：昵称。
- `user_profile_email`：额外的对外展示/联系邮箱（与登录 `email` 可不同，通过验证码二次确认修改）。
- `telegram_id`
- `phone_number`

**外部账号绑定**
- `user_profile_twitter_id`
- `user_profile_twitter_name`

**其他**
- `created_at`：创建时间，用于判断首次登录、异常行为等。

### 2. `email_verification_codes`

- `email`：邮箱。
- `code`：验证码（6 位数字）。
- `expires_at`：过期时间（10 分钟）。
- `ip_address`：请求 IP。
- `created_at`：用于限流和统计邮件量。

用途：
- 支持邮箱登录的验证码发送与验证。
- 支持更新 `user_profile_email` 时的验证码验证。

### 3. `point_transactions`

- `transaction_id`：主键。
- `userid`：用户。
- `points_change`：本次积分变化。
- `transaction_type`：交易类型：
  - `daily_login`：每日登录奖励。
  - `quiz`：答题奖励。
  - `comment_reward`：评论奖励。
  - 其他类型可能扩展。
- `user_local_date`：用户本地日期（每日登录判重使用）。
- `created_at_utc`：UTC 记录时间。

### 4. `purchase_records`

- Stripe 相关：
  - `stripe_checkout_session_id`
  - `stripe_payment_intent_id`
  - `stripe_customer_id`
  - `email_address`
  - `amount_total`（Stripe 为分，系统统一除以 100 转为美金）
  - `payment_status`
- 加密货币支付相关：
  - `wallet_address`
  - `payment_chain`（`solana` / `ethereum` / `base` / `monad` / `aptos`）
  - 多链交易哈希字段（如 `solana_transaction_hash`、`ethereum_transaction_hash` 等，对应 `CHAIN_TX_COLUMN_MAP`）
- 通用：
  - `user_id`：对应 `users.userid`
  - `currency`

用途：
- 记录所有会员购买行为。
- 配合链上扫描与 Stripe 统计，用于对账及排查漏记订单（`verify_payment_records` 系列接口）。

### 5. 推荐与风控相关表（简要）

- `reserve_info`：创新者会员机器人预约信息。
- `admin_whitelist`：管理员白名单（用于后台管理权限）。
- `detected_bot_users`：机器人刷分检测结果记录。
- `verify_payment_records`：多链/Stripe 的对账快照结果。

---

## 三、认证与登录流程

### 1. 发送邮箱验证码 `/auth/send-verification-code`

**主要步骤：**
1. 输入：`email`，同时携带 `recaptchaToken`（v3）与 `recaptchaV2Token`（v2）。
2. 先做“紧急邮件模式拦截”：部分 Hotmail 规则匹配到的明显机器邮箱将直接做“假发送”，但不会真正发送邮件。
3. 校验同一邮箱 30 秒冷却时间，防止频繁请求。
4. 使用 reCAPTCHA v3 与 v2 双重校验：
   - v3 `score` 必须高于 0.3。
   - v2 必须通过。
5. 生成 6 位验证码，写入 `email_verification_codes`（已存在时更新同一 email 记录）。
6. 统计当天发送总数，超过阈值（1500 起，每 500 一次）时给系统管理员发送告警邮件。
7. 发送验证邮件（HTML 模板），返回成功。

### 2. 验证邮箱验证码并建用户 `/auth/verify-code`

1. 输入：`email`，`code`。
2. 从 `email_verification_codes` 取出对应记录，校验：
   - 记录是否存在。
   - `code` 是否一致。
   - 是否过期。
3. 校验通过后，向 `users` 表插入 `email`（已存在则忽略），作为一个“邮箱侧用户”初始记录。

### 3. 核心登录保存 `/auth/save`

用于完成整套认证后，将登录态写入 `users`：

1. 入参：
   - `email`（可空，配合 `login_type` 与验证码使用）。
   - `code`（仅 `login_type == '0'` 时需要）。
   - `type`（`login_type`）。
   - `recaptchaToken`（再次做风控）。
   - `referrers_referral_code`（可选，注册时填写的推荐人码）。
2. 记录日志到 `auth_save_logs`，包括 email、IP、UA、reCAPTCHA 得分与状态。
3. 如果 reCAPTCHA 分数低于 0.5，则直接拒绝登录。
4. 当 `login_type == '0'` 时：
   - 通过 `_verify_email_code` 校验验证码。
5. 生成新的 `hash_code`（高熵随机串）。
6. 写入 `users`：
   - 若带 `referrers_referral_code`：
     - 首次创建用户时写入 `referrers_referral_code`。
     - 之后登录仅更新 `hash_code` 和 `login_type`，不覆盖已有推荐关系。
   - 不带推荐码时，只更新 `hash_code` 与 `login_type`。
7. 返回：`email` 与 `hash_code`，前端据此维持会话。

### 4. Token 验证与退出

- **校验 token** `/verify_token`
  - 按 `hash_code` 查询 `users`。
  - 找到则返回完整用户行；否则返回 `invalid`。

- **登出** `/logout`
  - 根据 `email` 查找用户。
  - 若存在，则随机生成新的 `hash_code` 更新，从逻辑上作废原 token（即“服务端旋转 token”）。

### 5. 管理员登录 `/api/admin-login`

- 管理员通过 **Solana 钱包签名**进行登录：
  - 客户端使用固定消息 `MESSAGE_TEXT` 进行签名。
  - 服务器使用 `verify_sol_sig` 验证签名。
- 验证通过后：
  - 生成 JWT `access_token`（30 分钟）、`refresh_token`，`role` 声明为 `admin`。
  - 后续部分后台接口使用 `@jwt_required()` + `get_jwt_identity()` 进行鉴权。

---

## 四、用户查询与邮箱/钱包绑定

### 1. 获取用户信息 `/api/get-users`

**用途：**
- 按邮箱或钱包地址获取用户信息，并在必要时自动创建钱包用户。
- 同时负责**邮箱与钱包互相绑定**。

**核心逻辑：**
1. 入参：
   - `email`（可选）、`wallet_address`（可选）、`chain`（默认 `solana`）、`token`（验证邮箱侧用户时需要）、`recaptcha_token`（防机器人）。
2. 通过 reCAPTCHA v3 校验，`score` 必须高于 0.2。
3. 校验 `chain` 属于配置的 `VALID_CHAINS` 之一。
4. 邮箱 / 钱包查询：
   - 有 `wallet_address` 时：
     - 通过 `CHAIN_COLUMN_MAP[chain]` 找到对应列（如 `solana_receive_address`）。
     - 在 `users` 中按该地址查找。
     - 若找到了钱包用户，且其 `linked_email` 不为空，则优先返回该邮箱用户的信息（即“邮箱是主身份”）。
     - 若没找到该钱包用户，则：
       - 调用链上接口检查该钱包在对应链是否有余额。
       - 有余额才允许创建用户记录，并分配新的 `hash_code`。
   - 有 `email` 时：
     - 要求必须附带 `token`，并按 `email + hash_code` 精确匹配用户。
5. 同时存在 `email` 与 `wallet_address` 时：
   - 若二者均找到对应用户：
     - 如果钱包用户已经是高等级会员（`Amplifier` 或 `Innovator`），则阻止将其绑到另一个邮箱账户上，防止滥用。
     - 对历史绑定关系进行“解绑再重绑”，确保：
       - 当前 email 的 `linked_wallet_address` 指向此钱包。
       - 当前 wallet 记录的 `linked_email` 指向此 email。
   - 绑定完成后，最终返回以邮箱用户为主的完整信息。
6. 若最终 email 与 wallet 都未查到，则返回 404。

### 2. 解除邮箱与钱包绑定 `/api/disconnect-wallet-from-email`

- 入参：`email`、`wallet_address`、`chain`、`token`。
- 通过 `email + hash_code` 找到邮箱用户，通过对应链列找到钱包用户。
- 若邮箱记录中的 `linked_wallet_address` 指向该钱包，则置为 `NULL`。
- 若钱包记录中的 `linked_email` 指向该邮箱，则置为 `NULL`。
- 如果两侧都没有找到有效绑定，则返回 404。

---

## 五、用户资料与外部联系方式

### 0. 个人信息编辑总览（Edit Personal Information）

- **前端入口**：用户在个人中心/Profile 页面修改昵称、社交账号、电话、对外邮箱等，最终都会落到本节的几个接口。
- **身份校验统一原则**：
  - 邮箱用户：必须携带 `email + token(hash_code)`，后端按 `email + hash_code` 精确匹配 `users`。
  - 钱包用户：必须携带 `wallet_address + chain + token(hash_code)`，后端按链路列 + `hash_code` 精确匹配。
  - 所有编辑类接口都会在找不到匹配用户或 token 失效时返回 401/403，防止越权修改他人资料。
- **字段更新策略**：
  - 只允许更新“白名单字段”（昵称、社交账号、电话、对外邮箱等），不会修改 `user_class`、积分、推荐码等敏感字段。
  - 采用 **动态 SQL**：仅对请求中实际出现的字段生成 `SET` 子句，避免无意覆盖为 `NULL`。
- **安全与审计**：
  - 对外邮箱修改强制二次邮箱验证码校验（见下一小节）。
  - Twitter 等第三方绑定通过 OAuth 回调写入，避免用户直接提交第三方 ID。

### 1. 更新基本资料 `/api/update-user-info`

- 入参可以包含：
  - `user_name`
  - `telegram_id`
  - `twitter_name` / `user_profile_twitter_name`
  - `phone_number`
  - 再加 `email` 或 `wallet_address + chain` 与 `token` 进行身份校验。
- 系统按照 `email + hash_code` 或 `wallet_address + chain + hash_code` 验证用户身份。
- 构造动态 SQL，只更新请求中实际提供的字段。

### 2. 更新用户对外邮箱 `/auth/update-user-profile-email/verify-code`

流程：
1. 用户请求给新邮箱发送验证码（重用 `/auth/send-verification-code` 逻辑）。
2. 前端拿到验证码后，调用本接口：
   - 入参：`email`（新邮箱）、`code`、`user_id`、`token`。
3. 服务端：
   - 使用 `_verify_email_code` 校验新邮箱与验证码。
   - 通过 `userid + hash_code` 再次校验登录态。
   - 更新 `users.user_profile_email` 为新邮箱。

### 3. Twitter OAuth 绑定

**发起绑定 `/auth/twitter/initiate`：**
- 入参：`email` 或 `wallet_address` + `chain`，以及 `token`。
- 按邮箱或钱包 + `hash_code` 找到对应用户 `userid`。
- 通过 `twitter_oauth` 模块构造 **带 state 的授权 URL**，state 中记录：
  - `uid`（userid）
  - 当前 token 的哈希（用于后续校验 token 未过期/未被替换）
  - 回跳 URL。

**回调 `/auth/twitter/callback`：**
- 解析并验证 state：
  - 包括签名与过期时间。
  - 验证其中 token 哈希与当前数据库中 `hash_code` 一致，防止中途用户登出或 token 被劫持。
- 使用授权码换取 Twitter access token，再调接口获取 `id` 与 `username`。
- 将 `user_profile_twitter_id`、`user_profile_twitter_name` 写入对应 `users` 记录。

---

## 六、会员等级与支付闭环

### 1. Stripe 支付与会员升级

**创建支付会话 `/api/create-stripe-checkout-session`：**
- 入参：`user_id`、`membership_type`（`Amplifier Membership` / `Innovator Membership`）。
- 根据会员类型决定金额：
  - Amplifier：`9900`（即 99 美金）。
  - Innovator：`39900`（即 399 美金）。
- 创建 Stripe Checkout Session，返回前端跳转 URL。

**Webhook 回调 `/api/stripe-payment-completed`：**
- 验证签名（`STRIPE_WEBHOOK_SECRET_LIVE`）。
- 只处理 `checkout.session.completed`：
  - 记录订单到 `purchase_records`。
  - 若 `payment_status == 'paid'` 且 `metadata.user_id` 存在：
    - 查询当前 `user_class`。
    - 规则：
      - `Explorer Member` 支付 99 美金 → 升级为 `Amplifier Member`。
      - `Amplifier Member` 支付 399 美金 → 升级为 `Innovator Member`。
    - 其他组合不会升级（比如已经是高等级会员再次购买低等级）。

### 2. 加密货币支付与会员升级 `/api/record-crypto-payment`

1. 入参：`wallet_address`、`amount_total`（整数，单位“美元”）、`user_id`、`transaction_hash`、`currency`、`chain`。
2. 确认 `chain` 合法。
3. 如有 `transaction_hash`：
   - 先检查该哈希是否已存在于任一链交易哈希列，防止重复录入。
   - 调用不同链的 `verify_*_payment` 函数，对链上 transfer 进行校验：
     - 收款地址必须为 Prismax 官方地址。
     - 金额必须在 99 或 399 美金的允许误差范围内。
4. 交易合法后，写入 `purchase_records`，标记 `payment_status = 'paid'`。
5. 使用与 Stripe 相同的规则升级会员等级：
   - 99 美金：仅当当前为 `Explorer Member` 时升级为 `Amplifier Member`。
   - 399 美金：仅当当前为 `Amplifier Member` 时升级为 `Innovator Member`。

---

## 七、积分系统与用户激励

### 1. 每日登录积分 `/api/daily-login-points`

**行为：**
- 支持用 `wallet_address + chain` 或 `email` 查找用户。
- 校验 `chain` 合法，并允许用户传入 `user_local_date`（限制必须在当前 UTC 日期 ±1 天）。
- 逻辑：
  1. 若 `total_points == 0`，视为第一次积分初始化：
     - 赠送 `1000 * multiplier` 积分，`multiplier` 在 Monad 链为 2，其它为 1。
  2. 检查当天是否已有 `daily_login` 记录：
     - 没有则按照会员等级给每日登录积分：
       - `Explorer Member`：10 积分。
       - 其他普通会员：30 积分。
       - `Innovator Member`：50 积分（代码中对 Innovator 单独提升）。
       - 再乘以 `multiplier`（Monad 链加倍）。
     - 有则不再发放，只返回已领取状态。
  3. 写入 `point_transactions` 并更新 `users.total_points`。

### 2. 查询积分明细 `/api/get-point-transactions`

- 可使用 `wallet_address + chain` 或 `email`，或不带参数：
  - 带参数时，返回该用户最近 14 天的积分记录，并附上当前 `total_points`。
  - 不带参数时，返回所有用户最近 14 天的记录（用于后台查看）。

### 3. 推荐关系与推荐奖励 `/api/get-users-by-referral`

**场景：**
- 某用户作为推荐人，希望查看自己推荐的用户及获得的推荐奖励（邀请奖励 + 10% 分成）。

**结算规则：**
1. 入参：`referrers_referral_code`（当前用户的推荐码）、`userid`（当前用户）、`token`。
2. 通过 `userid + hash_code` 锁定并锁行，防止并发多次结算。
3. 校验 `referrers_referral_code` 必须等于该用户在 `users.referral_code` 中的值。
4. 查询所有 `users.referrers_referral_code = referral_code` 的被推荐人，累加其 `total_points`。
5. **邀请奖励部分**：
   - 每个被推荐人固定 500 积分。
   - 使用 `referral_initial_reward` 累积已发放的邀请奖励，按差值补发，确保不会重复发。
6. **10% 分成部分**：
   - `target = floor(所有被推荐人 total_points 之和 * 10%)`。
   - 使用 `referred_reward_point` 记录已结算金额，只发放增量部分。
7. 最终返回：
   - 被推荐用户列表。
   - 当前推荐奖励总额（邀请奖励 + 10% 分成折算后的积分和）。

### 4. 测验积分 `/api/quiz/check-status` 与 `/api/quiz/submit`

- `check-status`：查询用户是否已经有 `transaction_type = 'quiz'` 的积分记录，返回是否完成及积分数。
- `submit`：
  - 入参：`userid`、`correct_answers`、`total_questions`、`recaptchaToken`。
  - 通过 reCAPTCHA 校验。
  - 若已存在 `quiz` 类型记录，则拒绝重复提交。
  - 积分计算：
    - 每个正确答案 500 分。
    - 全部答对再额外奖励 1000 分。
  - 写入 `point_transactions` 和 `users.total_points`。

### 5. 评论奖励 `/api/check-comment-reward`

- 限流：每个 `user_id` 每分钟最多 5 次调用。
- 校验评论是否“有意义”：
  - 至少 10 个字符，且至少 3 个单词。
- 每日每个用户仅可获得一次评论奖励：
  - 通过检查当天是否存在 `transaction_type = 'comment_reward'` 的记录。
- 奖励积分：
  - 若用户为 `Explorer Member`：50 分。
  - 其他会员：150 分。
- 并写入 `point_transactions` 与 `users.total_points`。

---

## 八、与机器人/运维相关的用户逻辑

### 1. 机器人预约 `/api/reserve-robot`

- 仅对 `Innovator Member` 开放（根据 `users.user_class` 校验）。
- 要求：
  - `user_id` 与 `token` 一致。
  - 填写邮箱、姓名、电话、机器人名称等信息。
- 保存到 `reserve_info`，并异步发送预约说明邮件。

### 2. 三种 TeleOp 机械臂与会员权限（arm1/arm2/arm3）

- **机械臂概览**
  - `arm1`：Training Arm（训练臂，常规练习与积分获取）。
  - `arm2`：Monad Arm（活动臂，对应 Monad 排行与奖励活动）。
  - `arm3`：Buddy Arm（Buddy 臂，偏向新人体验与高等级会员特权）。

- **Explorer Member**
  - 禁止使用所有机器人：尝试加入 `arm1/arm2/arm3` 任意队列将直接返回 **403**，统一文案为 `"Explorer tier cannot use robots"`。
  - 因此 Explorer 不会在 `tele_op_control_history` 中形成新的 TeleOp 控制记录。

- **Amplifier Member**
  - `arm1`（Training Arm）：
    - 按 **UTC 自然日**统计入队次数，每日最多成功入队 **3 次**（基于 `robot_queue.created_at`）。
    - 第 4 次及之后尝试入队将返回 403，错误信息中包含 “arm1 ... 3 times per day (UTC)”。
  - `arm3`（Buddy Arm）：
    - 针对 `arm3` 采用 **终身总次数**限制：累计成功使用 **3 次**后，再次入队会返回 403，错误信息中包含 “3 total uses limit for arm3”。
    - 该统计基于 `tele_op_control_history.robot_id = 'arm3'`。
  - `arm2`（Monad Arm）：
    - 当前版本在会员维度**无额外单独次数限制**，仅受通用排队/互斥与 Fast Track 规则约束（详见 TeleOp 服务说明），可正常加入队列并控制。

- **Innovator Member**
  - 可使用 **所有机器人**（`arm1/arm2/arm3`），不受 Explorer 的全局禁用规则限制。
  - Fast Track（抢占队列）配额从“每台机器人 8 次/日”统一调整为：
    - **“全机器人合计每天 6 次 Fast Track”**：当日第 1–6 次 Fast Track 请求正常生效；
    - 第 7 次及之后请求时接口仍允许入队，但不再标记为 Fast Track，并返回提示 `"maximum 6 fast track a day"`。
  - 这 6 次 Fast Track 配额在 `arm1/arm2/arm3` 之间**共享**，由 `tele_op_control_history` 与队列逻辑联合控制。

- **通用队列互斥（所有会员等级生效）**
  - 用户若在任一机器人队列中处于 `waiting/active` 状态，尝试加入另一台机器人队列会被拒绝，统一返回 403，提示已在其他机器人队列中。
  - 该规则对 `arm1/arm2/arm3` 一视同仁，防止同一账号并发占用多台机器人。

### 3. 用户统计 `/api/user-stats`

- 需 JWT 管理员权限。
- 返回：
  - 各会员等级用户数量（Innovator/Amplifier/Explorer）。
  - `tele_op_control_history` 中有操作记录的唯一 `user_id` 数量（远程操作活跃用户数）。

### 4. 管理端相关（简要）

- `admin_whitelist` 的增删查接口：用于配置后台可操作钱包地址。
- `detect_and_reset_bots()`：
  - 检测未来日期或在项目启动前的积分交易，识别疑似刷分账户，记录到 `detected_bot_users`，并为后续积分重置做准备。

---

## 九、小结：Prismax 用户管理的关键要点

- **统一会话模型**：所有登录方式最终都收敛到 `users` 表与 `hash_code` 令牌。
- **多入口同身份**：通过 `linked_email` 与 `linked_wallet_address`，实现邮箱 + 多链钱包统一账户视图。
- **会员等级驱动业务**：会员等级影响积分倍率、机器人预约资格等关键权益，并与支付闭环强绑定。
- **积分体系丰富且防刷**：多种行为驱动积分增长，同时通过 reCAPTCHA、邮箱模式黑名单、时间区间检测等手段抑制机器人行为。
- **支付与对账机制完备**：Stripe 与多链支付均有记录表和对账快照机制，支持后续财务与风控分析。

---

## Prismax User Management Business Logic (app_prismax_user_management) – English Version

This document summarizes the core business logic of Prismax user management (user_management) based on `app_prismax_user_management/app.py` and related helper modules, for requirements, testing, and debugging reference.

---

## 1. Overall Overview

- **Coexistence of identity identifiers and login methods**
  - Supports **email verification-code login** (passwordless), third-party login (Google/Apple, distinguished by `login_type`), and **multi-chain wallet login** (Solana/Ethereum/Base/Monad/Aptos).
  - The system uniformly uses `users.hash_code` as the long-lived login token. The frontend typically sends it back via `Authorization: Bearer <hash_code>` for authentication.

- **Multi-role / membership tier system**
  - The `users.user_class` field defines membership tiers:
    - `Explorer Member`: default free user.
    - `Amplifier Member`: upgraded via a $99 payment.
    - `Innovator Member`: further upgraded via a $399 payment.
  - Some **advanced features** are only available to specific tiers, for example:
    - **TeleOp robot remote control**:
      - Explorer: completely blocked from using all TeleOp robots (joining any `arm1/arm2/arm3` queue returns 403).
      - Amplifier:
        - Training Arm (`arm1`): at most **3 successful queue joins per UTC day** (counted by `robot_queue.created_at`); the 4th and later attempts return 403.
        - Buddy Arm (`arm3`): at most **3 lifetime uses** in total for TeleOp sessions (counted from `tele_op_control_history.robot_id='arm3'`).
        - Monad Arm (`arm2`): currently has **no additional per-tier usage cap**; it is only constrained by the generic queue / Fast Track rules.
        - Amplifier users **cannot** reserve robots.
      - Innovator: has access to all TeleOp features, including Fast Track queue-jumping and all three arms, and enjoys higher point multipliers.
    - **Robot reservation `/api/reserve-robot`**:
      - Only available to Innovator Members, used to book in-person demos or remote TeleOp experiences (requires `user_id + token` verification).
    - **Fast Track (TeleOp queue jump)**:
      - Only Innovators can use Fast Track, with a shared limit of 6 Fast Track uses per UTC day across `arm1/arm2/arm3`.

- **Dual-channel account system: multi-chain wallets + email**
  - Users can enter the system either via **email** or via **wallet address**.
  - `linked_email` and `linked_wallet_address` bind the “email account” and “wallet account” so they are treated as the same user identity.

- **Deep coupling between points and entitlements**
  - Points accumulation methods: first-login bonus, daily login, quizzes, comment rewards, referral revenue share, etc., all managed via `point_transactions` + `users.total_points`.
  - Membership tier is tied to points multipliers (e.g., Innovator earns higher daily points).

- **Payment and membership-upgrade closed loop**
  - Stripe payments (credit card) and multi-chain crypto payments (Solana/EVM/Base/Monad/Aptos) are all recorded in `purchase_records`.
  - When payment amounts meet certain thresholds, the user’s membership tier is automatically upgraded from `Explorer → Amplifier → Innovator`.

- **External service bindings**
  - Twitter OAuth: bound into `user_profile_twitter_id` and `user_profile_twitter_name` on the user record.
  - YouTube is used only for monitoring/alerting; it does not directly affect user identity but is related to `robot_status` and admin notifications.

---

## 2. Core Data Structures (Tables and Key Fields)

> The following fields are inferred from SQL queries and update logic; the actual DDL in the database is authoritative.

### 1. `users` Table (Primary User Table)

**Identity and login related**
- `userid`: primary key, auto-increment.
- `email`: login email (nullable, used for the email-based account system).
- `login_type`: login method; `'0'` means email verification-code login, other values are used for Google/Apple, etc.
- `hash_code`: current login token, equivalent to a “session/long-term login token”, refreshed on each successful login or logout.

**Wallet and on-chain addresses (multi-chain)**
- `solana_receive_address`
- `ethereum_receive_address`
- `base_receive_address`
- `monad_receive_address`
- `aptos_receive_address`

**Binding between email and wallet**
- `linked_email`: email bound to a wallet user.
- `linked_wallet_address`: wallet address bound to an email user (the specific chain is determined at runtime).

**Membership and points system**
- `user_class`: membership tier (`Explorer Member` / `Amplifier Member` / `Innovator Member`).
- `total_points`: current total available points.
- `referral_code`: the referral code this user shares externally.
- `referrers_referral_code`: the referral code of the referrer that this user entered when registering (i.e., “who invited me”).
- `referred_reward_point`: settled points from the 10% revenue share, used to avoid double-counting.
- `referral_initial_reward`: accumulated total of initial invite rewards (500 points per invitee) that have been issued.

**Profile / contact information**
- `user_name`: nickname.
- `user_profile_email`: an additional public/contact email (can be different from login `email`, updated via verification code).
- `telegram_id`
- `phone_number`

**External account bindings**
- `user_profile_twitter_id`
- `user_profile_twitter_name`

**Others**
- `created_at`: creation timestamp, used to determine first login, abnormal behavior, etc.

### 2. `email_verification_codes`

- `email`: email address.
- `code`: 6-digit verification code.
- `expires_at`: expiration time (10 minutes).
- `ip_address`: request IP.
- `created_at`: used for rate-limiting and daily email volume statistics.

Usage:
- Supports sending and verifying verification codes for email login.
- Supports verifying codes when updating `user_profile_email`.

### 3. `point_transactions`

- `transaction_id`: primary key.
- `userid`: user ID.
- `points_change`: points change for this transaction.
- `transaction_type`: transaction type:
  - `daily_login`: daily login reward.
  - `quiz`: quiz reward.
  - `comment_reward`: comment reward.
  - other types may be added.
- `user_local_date`: user’s local date (used to deduplicate daily login).
- `created_at_utc`: UTC timestamp.

### 4. `purchase_records`

- Stripe-related:
  - `stripe_checkout_session_id`
  - `stripe_payment_intent_id`
  - `stripe_customer_id`
  - `email_address`
  - `amount_total` (Stripe reports cents; the system divides by 100 to convert to USD).
  - `payment_status`
- Crypto payment related:
  - `wallet_address`
  - `payment_chain` (`solana` / `ethereum` / `base` / `monad` / `aptos`)
  - Multi-chain transaction hash fields (e.g., `solana_transaction_hash`, `ethereum_transaction_hash`, etc., mapped by `CHAIN_TX_COLUMN_MAP`)
- Common:
  - `user_id`: corresponds to `users.userid`
  - `currency`

Usage:
- Records all membership purchase behaviors.
- Together with on-chain scanning and Stripe statistics, used for reconciliation and investigating missed/incorrect orders (`verify_payment_records` APIs).

### 5. Referral and risk control related tables (brief)

- `reserve_info`: robot reservation information for Innovator members.
- `admin_whitelist`: admin whitelist (for backend management permissions).
- `detected_bot_users`: records detected bot/abuse users.
- `verify_payment_records`: reconciliation snapshots for multi-chain/Stripe.

---

## 3. Authentication and Login Flows

### 1. Send Email Verification Code `/auth/send-verification-code`

**Main steps:**
1. Input: `email`, together with `recaptchaToken` (v3) and `recaptchaV2Token` (v2).
2. Run “emergency email mode interception”: obvious bot-like Hotmail addresses matching certain patterns are short-circuited as “fake send” (no real email is sent).
3. Enforce a 30-second cooldown per email address to prevent frequent requests.
4. Use both reCAPTCHA v3 and v2 checks:
   - v3 `score` must be greater than 0.3.
   - v2 must pass.
5. Generate a 6-digit code and write it into `email_verification_codes` (update existing rows for the same email).
6. Count the number of emails sent on the current day, and when thresholds are exceeded (starting from 1,500, then every 500), send alert emails to system admins.
7. Send the verification email (HTML template) and return success.

### 2. Verify Email Code and Create User `/auth/verify-code`

1. Input: `email`, `code`.
2. Look up the record in `email_verification_codes` and validate:
   - whether the record exists,
   - whether `code` matches,
   - whether it is expired.
3. Once validated, insert a `users` row with this `email` (ignore if it already exists), as an initial “email-side user” record.

### 3. Core Login Save `/auth/save`

Used to finalize authentication and persist login state into `users`:

1. Input:
   - `email` (optional, used with `login_type` and email verification code).
   - `code` (required only when `login_type == '0'`).
   - `type` (i.e., `login_type`).
   - `recaptchaToken` (for an additional risk check).
   - `referrers_referral_code` (optional, referral code provided at registration).
2. Log into `auth_save_logs`, including email, IP, UA, reCAPTCHA score and status.
3. If the reCAPTCHA score is below 0.5, reject login directly.
4. When `login_type == '0'`:
   - Use `_verify_email_code` to validate the email code.
5. Generate a new `hash_code` (high-entropy random string).
6. Write to `users`:
   - If `referrers_referral_code` is provided:
     - On first creation, write `referrers_referral_code`.
     - On subsequent logins, only update `hash_code` and `login_type`, without overwriting existing referral relationships.
   - If no referral code is provided, only update `hash_code` and `login_type`.
7. Return: `email` and `hash_code`, which the frontend uses to maintain the session.

### 4. Token Verification and Logout

- **Verify token** `/verify_token`
  - Query `users` by `hash_code`.
  - If found, return the full user row; otherwise, return `invalid`.

- **Logout** `/logout`
  - Look up the user by `email`.
  - If found, generate a new random `hash_code` and update it, which effectively invalidates the old token (server-side token rotation).

### 5. Admin Login `/api/admin-login`

- Admins log in via **Solana wallet signature**:
  - The client signs a fixed message `MESSAGE_TEXT`.
  - The server uses `verify_sol_sig` to verify the signature.
- Upon success:
  - Generate a JWT `access_token` (30 minutes) and `refresh_token`, with `role` claim set to `admin`.
  - Some backend admin APIs use `@jwt_required()` + `get_jwt_identity()` for authorization.

---

## 4. User Query and Email/Wallet Binding

### 1. Get User Info `/api/get-users`

**Purpose:**
- Fetch user information by email or wallet address, and create a wallet user when necessary.
- Also responsible for **binding email and wallet to each other**.

**Core logic:**
1. Input:
   - `email` (optional), `wallet_address` (optional), `chain` (defaults to `solana`), `token` (required when validating an email-side user), `recaptcha_token` (anti-bot).
2. Validate reCAPTCHA v3; `score` must be greater than 0.2.
3. Validate that `chain` belongs to one of the configured `VALID_CHAINS`.
4. Email / wallet query:
   - When `wallet_address` is provided:
     - Use `CHAIN_COLUMN_MAP[chain]` to determine the column (e.g., `solana_receive_address`).
     - Query `users` by this on-chain address.
     - If a wallet user is found and its `linked_email` is not empty, return the corresponding email user info instead (treating email as the primary identity).
     - If the wallet user is not found:
       - Call on-chain APIs to check if the wallet has a balance on the given chain.
       - Only if the wallet has a balance is a new user record created and a new `hash_code` assigned.
   - When `email` is provided:
     - `token` is required and must match `email + hash_code` exactly.
5. When both `email` and `wallet_address` are provided:
   - If both are found:
     - If the wallet user is already a high-tier member (`Amplifier` or `Innovator`), prevent it from being bound to another email account to avoid abuse.
     - Perform “unbind then rebind” of historical relationships, ensuring:
       - The current email’s `linked_wallet_address` points to this wallet.
       - The current wallet record’s `linked_email` points to this email.
   - After binding is finalized, return the email-side user’s full information as the primary identity.
6. If neither email nor wallet ultimately resolves to a user, return 404.

### 2. Unbind Email and Wallet `/api/disconnect-wallet-from-email`

- Input: `email`, `wallet_address`, `chain`, `token`.
- Find the email user via `email + hash_code`, and the wallet user via the chain-specific address column.
- If the email record’s `linked_wallet_address` points to that wallet, set it to `NULL`.
- If the wallet record’s `linked_email` points to that email, set it to `NULL`.
- If neither side has a valid binding, return 404.

---

## 5. User Profile and External Contact Information

### 0. Edit Personal Information – Overview

- **Frontend entry:** When users change nickname, social accounts, phone number, or public email on the Profile page, these changes are processed by the APIs in this section.
- **Unified identity verification:**
  - Email users: must provide `email + token(hash_code)`; the backend matches `users` by `email + hash_code`.
  - Wallet users: must provide `wallet_address + chain + token(hash_code)`; the backend matches via the chain column + `hash_code`.
  - All edit-type APIs return 401/403 if no matching user is found or the token is invalid, preventing unauthorized edits to other users’ data.
- **Field update strategy:**
  - Only “whitelisted fields” (nickname, social accounts, phone number, public email, etc.) can be updated; sensitive fields such as `user_class`, points, and referral codes cannot be modified here.
  - Uses **dynamic SQL**: only generates `SET` clauses for fields actually present in the request to avoid inadvertently setting fields to `NULL`.
- **Security and auditing:**
  - Updating the public email requires an additional email verification-code check (see the next subsection).
  - Twitter and other third-party bindings are written via OAuth callbacks to avoid the user directly submitting third-party IDs.

### 1. Update Basic Profile `/api/update-user-info`

- Input may include:
  - `user_name`
  - `telegram_id`
  - `twitter_name` / `user_profile_twitter_name`
  - `phone_number`
  - Plus `email` or `wallet_address + chain` with `token` for identity verification.
- The system verifies identity using either `email + hash_code` or `wallet_address + chain + hash_code`.
- Dynamic SQL is constructed to update only the fields actually provided in the request.

### 2. Update Public Email `/auth/update-user-profile-email/verify-code`

Flow:
1. The user requests a verification code to be sent to the new email (reuses the `/auth/send-verification-code` logic).
2. After receiving the code, the frontend calls this API:
   - Input: `email` (new email), `code`, `user_id`, `token`.
3. On the server:
   - Use `_verify_email_code` to validate the new email and code.
   - Revalidate login state using `userid + hash_code`.
   - Update `users.user_profile_email` to the new email.

### 3. Twitter OAuth Binding

**Initiate binding `/auth/twitter/initiate`:**
- Input: `email` or `wallet_address + chain`, and `token`.
- Locate `userid` using email or wallet + `hash_code`.
- Use the `twitter_oauth` module to construct a **stateful authorization URL**, where the state includes:
  - `uid` (userid),
  - hash of the current token (to validate that the token is not expired or replaced),
  - callback URL.

**Callback `/auth/twitter/callback`:**
- Parse and validate the state:
  - includes signature and expiry.
  - verify that the token hash in state matches the current `hash_code` in the database, preventing issues if the user logged out or the token was hijacked in the meantime.
- Use the authorization code to obtain a Twitter access token and call Twitter APIs to get `id` and `username`.
- Write `user_profile_twitter_id` and `user_profile_twitter_name` into the corresponding `users` record.

---

## 6. Membership Tiers and Payment Closed Loop

### 1. Stripe Payments and Membership Upgrade

**Create checkout session `/api/create-stripe-checkout-session`:**
- Input: `user_id`, `membership_type` (`Amplifier Membership` / `Innovator Membership`).
- Decide the amount based on membership type:
  - Amplifier: `9900` (i.e., $99).
  - Innovator: `39900` (i.e., $399).
- Create a Stripe Checkout Session and return the URL for the frontend to redirect.

**Webhook callback `/api/stripe-payment-completed`:**
- Verify signature with `STRIPE_WEBHOOK_SECRET_LIVE`.
- Only handle `checkout.session.completed` events:
  - Record the order into `purchase_records`.
  - If `payment_status == 'paid'` and `metadata.user_id` exists:
    - Query the current `user_class`.
    - Rules:
      - `Explorer Member` paying $99 → upgrade to `Amplifier Member`.
      - `Amplifier Member` paying $399 → upgrade to `Innovator Member`.
    - Other combinations do not trigger upgrades (e.g., already high-tier members buying lower-tier products).

### 2. Crypto Payments and Membership Upgrade `/api/record-crypto-payment`

1. Input: `wallet_address`, `amount_total` (integer, in USD), `user_id`, `transaction_hash`, `currency`, `chain`.
2. Validate that `chain` is allowed.
3. If `transaction_hash` is provided:
   - First check whether this hash already exists in any chain’s transaction-hash column to prevent duplicate entries.
   - Call the appropriate `verify_*_payment` function per chain to validate the on-chain transfer:
     - The recipient address must be the official Prismax address.
     - Amount must be within the allowed tolerance for $99 or $399.
4. Once the transaction is valid, write it into `purchase_records` with `payment_status = 'paid'`.
5. Apply the same membership-upgrade rules as Stripe:
   - $99: upgrade to `Amplifier Member` only if the current tier is `Explorer Member`.
   - $399: upgrade to `Innovator Member` only if the current tier is `Amplifier Member`.

---

## 7. Points System and User Incentives

### 1. Daily Login Points `/api/daily-login-points`

**Behavior:**
- Supports lookup via `wallet_address + chain` or `email`.
- Validates `chain`, and allows the user to pass `user_local_date` (must be within ±1 day of the current UTC date).
- Logic:
  1. If `total_points == 0`, treat it as initialization:
     - Grant `1000 * multiplier` points; `multiplier` is 2 on Monad chain and 1 on others.
  2. Check whether there is already a `daily_login` record for that date:
     - If not, award daily login points by membership tier:
       - `Explorer Member`: 10 points.
       - Other regular members: 30 points.
       - `Innovator Member`: 50 points (Innovator is explicitly boosted in code).
       - Then multiply by `multiplier` (double on Monad).
     - If yes, do not issue additional points; just return “already claimed”.
  3. Write a record into `point_transactions` and update `users.total_points`.

### 2. Query Points History `/api/get-point-transactions`

- Can be called with `wallet_address + chain` or `email`, or with no parameters:
  - With parameters: returns the user’s last 14 days of point transactions plus current `total_points`.
  - Without parameters: returns all users’ point transactions for the last 14 days (for backend viewing).

### 3. Referral Relationships and Rewards `/api/get-users-by-referral`

**Scenario:**
- A user, as a referrer, wants to see the users they have referred and the rewards they have earned (fixed invite rewards + 10% revenue share).

**Settlement rules:**
1. Input: `referrers_referral_code` (the current user’s referral code), `userid` (current user), `token`.
2. Use `userid + hash_code` to lock and lock the row, preventing concurrent multiple settlements.
3. Validate that `referrers_referral_code` equals the user’s own `users.referral_code` value.
4. Query all users with `users.referrers_referral_code = referral_code` and sum their `total_points`.
5. **Invite rewards:**
   - Each referred user yields a fixed 500 points.
   - Use `referral_initial_reward` to record cumulative invite rewards; only pay the difference to avoid duplication.
6. **10% revenue share:**
   - `target = floor(sum_of_all_referred_users_total_points * 10%)`.
   - Use `referred_reward_point` to record settled amounts and only grant incremental rewards.
7. The response includes:
   - the referred user list,
   - the current total reward for referrals (invite reward + 10% revenue share converted to points).

### 4. Quiz Points `/api/quiz/check-status` and `/api/quiz/submit`

- `check-status`: check whether the user already has a `transaction_type = 'quiz'` record, and return whether completed and how many points.
- `submit`:
  - Input: `userid`, `correct_answers`, `total_questions`, `recaptchaToken`.
  - Validate via reCAPTCHA.
  - If there is already a `quiz` record, reject duplicate submissions.
  - Points calculation:
    - 500 points per correct answer.
    - Extra 1,000 points if all answers are correct.
  - Write to `point_transactions` and update `users.total_points`.

### 5. Comment Reward `/api/check-comment-reward`

- Rate limiting: each `user_id` can call this API at most 5 times per minute.
- Validate that the comment is “meaningful”:
  - at least 10 characters and at least 3 words.
- Each user can only receive one comment reward per day:
  - ensured by checking for existing `transaction_type = 'comment_reward'` records for that day.
- Reward points:
  - `Explorer Member`: 50 points.
  - Other members: 150 points.
- Also writes to `point_transactions` and updates `users.total_points`.

---

## 8. User Logic Related to Robots and Operations

### 1. Robot Reservation `/api/reserve-robot`

- Only open to `Innovator Member` (validated via `users.user_class`).
- Requirements:
  - `user_id` and `token` must match.
  - Fill in email, name, phone, robot name, and other information.
- Save into `reserve_info` and asynchronously send a reservation information email.

### 2. Three TeleOp Arms and Membership Permissions (arm1/arm2/arm3)

- **Arm overview**
  - `arm1`: Training Arm, for regular practice and earning points.
  - `arm2`: Monad Arm, associated with the Monad leaderboard and campaign rewards.
  - `arm3`: Buddy Arm, focused on first-time users and premium member privileges.

- **Explorer Member**
  - Forbidden from using all robots: attempting to join any of `arm1/arm2/arm3` queues returns **403** with the unified message `"Explorer tier cannot use robots"`.
  - Therefore, Explorers will not generate new TeleOp control records in `tele_op_control_history`.

- **Amplifier Member**
  - `arm1` (Training Arm):
    - Daily queue-join limit per UTC day: at most **3 successful queue joins** (based on `robot_queue.created_at`).
    - The 4th and later attempts return 403 with an error message containing “arm1 ... 3 times per day (UTC)”.
  - `arm3` (Buddy Arm):
    - Lifetime total limit: max **3 successful uses** of `arm3`. On and after the 4th, joining the queue returns 403 with “3 total uses limit for arm3”.
    - This is counted from `tele_op_control_history.robot_id = 'arm3'`.
  - `arm2` (Monad Arm):
    - Currently has **no additional member-specific usage limit**; only general queue/mutual-exclusion and Fast Track rules apply (see TeleOp service docs). Amplifiers can join and control normally.

- **Innovator Member**
  - Can use **all robots** (`arm1/arm2/arm3`), unaffected by the Explorer global prohibition.
  - Fast Track (queue jump) quota is unified from “8 times per day per robot” to:
    - **“6 Fast Track uses per day across all robots”**: the first 6 Fast Track requests per UTC day are honored;
    - The 7th and later requests still allow queue joining but are not marked as Fast Track, and the response includes `"maximum 6 fast track a day"`.
  - These 6 Fast Track uses are **shared** across `arm1/arm2/arm3`, enforced via `tele_op_control_history` and the queue logic.

- **Global queue mutual exclusion (applies to all tiers)**
  - If a user is in `waiting/active` state in any robot queue, attempts to join another robot’s queue are rejected with 403 and a message indicating they are already in another robot’s queue.
  - This rule applies equally to `arm1/arm2/arm3`, preventing a single account from concurrently occupying multiple robots.

### 3. User Stats `/api/user-stats`

- Requires JWT admin permissions.
- Returns:
  - the number of users per membership tier (Innovator/Amplifier/Explorer);
  - the unique count of `user_id` values with records in `tele_op_control_history` (active remote-control users).

### 4. Admin-Side Related (Brief)

- CRUD APIs for `admin_whitelist`: used to configure wallet addresses allowed to operate from the backend.
- `detect_and_reset_bots()`:
  - detects point transactions with dates in the future or before the project launch, identifies suspected bot accounts, records them into `detected_bot_users`, and prepares for subsequent point resets.

---

## 9. Summary: Key Takeaways of Prismax User Management

- **Unified session model**: all login methods converge on the `users` table and `hash_code` token.
- **Unified identity across multiple entry points**: via `linked_email` and `linked_wallet_address`, email and multi-chain wallets form a unified account view.
- **Membership-tier-driven business**: membership tier affects point multipliers, robot reservation eligibility, and other key entitlements, and is tightly coupled with the payment closed loop.
- **Rich yet anti-abuse points system**: multiple behaviors drive point growth, while reCAPTCHA, email pattern blacklists, and time-window checks help mitigate bot abuse.
- **Complete payment and reconciliation mechanisms**: Stripe and multi-chain payments have dedicated tables and reconciliation snapshots to support finance and risk analysis.
