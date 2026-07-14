# Prisma(x) Forum

一个社区讨论 / “数字专著”论坛，是对 `Prisma Discussion` 设计原型的生产化重建。

- **后端**：FastAPI + SQLite（SQLAlchemy），端口 **8085**
- **前端**：Next.js（App Router，TypeScript），端口 **3001**
- **认证**：可插拔适配器。当前提供一个自包含的 demo 登录，同时预留 PrismaX 自有用户系统的接入位置，见 [认证集成](#认证集成)。

浏览器只和 Web 源站（`:3001`）通信；Next 服务会把 `/api/*` 代理到后端（见 `frontend/next.config.ts`）。因此不需要处理 CORS，也不需要处理跨域 cookie，并且可以在任意 host 或代理后运行。生产环境中 API 绑定到 loopback，不对公网暴露。

```text
prismax-forum/
├── backend/    FastAPI 应用、SQLite 数据库、seed 脚本
└── frontend/   Next.js 应用，忠实移植原型 UI
```

## 功能

浏览帖子（分类筛选、Latest / Most Discussed 排序、搜索、分页）· 阅读带 block 内容的文章（标题、引用、列表、代码、图片）· 点赞与收藏 · 嵌套评论与回复 · 支持封面图、草稿和发布的 block-based 编辑器。

---

## 运行

### 1. 后端（端口 8085）

```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # 首次运行
cp .env.example .env                # 可选；本地 demo 默认配置可直接使用
.venv/bin/python -m app.seed        # 加载原型内容，幂等
./run.sh                            # 在 0.0.0.0:8085 启动 uvicorn
```

健康检查：`curl localhost:8085/api/health`

交互式 API 文档：`http://localhost:8085/docs`

### 2. 前端（端口 3001）

```bash
cd frontend
npm install        # 首次运行
npm run dev        # 在 0.0.0.0:3001 启动开发服务
# 或：npm run build && npm start   # 生产模式
```

打开 `http://localhost:3001`（或从 VM 外部访问 `http://34.186.168.140:3001`，端口 3000-9000 已开放）。

> 前端会在自己的 origin 上调用 `/api/*`；Next 会把这些请求代理到后端（`BACKEND_ORIGIN`，默认 `http://localhost:8085`）。如果是前后端分离部署，API 位于不同 origin，可以改用 `NEXT_PUBLIC_API_BASE`。

### 此 VM 上的生产运行方式（systemd，已在运行）

前后端都以 **systemd user units** 运行（遵循此处其他服务的约定），因此可以在登出或重启后继续存活。Web 在公网 `:3001` 可访问；API 只监听 loopback。

```bash
export XDG_RUNTIME_DIR=/run/user/$(id -u)   # 非 login shell 中需要设置
systemctl --user status  prismax-forum-{api,web}
systemctl --user restart prismax-forum-{api,web}
journalctl --user -u prismax-forum-web -f   # 或 tail /mnt/data/home/alex/logs/prismax-forum-*.log
```

修改前端代码后，需要先重新构建再重启 Web unit：

`cd frontend && npm run build && systemctl --user restart prismax-forum-web`

### Demo 登录

点击 **Sign In**，选择一个预设身份（You、Dr. Thorne 等），或输入任意名字。

这是一个 **stub**。替换为 PrismaX 真实认证方式见下文。

---

## 认证集成

> **这是 PrismaX 最关心的部分。** 论坛不会构建自己的用户系统。所有身份都通过一个接口进入，由 `AUTH_PROVIDER` 环境变量选择。切换 provider 不需要修改任何论坛业务代码。

### 接线方式

```text
request ─▶ AuthAdapter.identify(request) ─▶ Identity ─▶ upsert local users row ─▶ User
            (demo | prismax)                (external_id, name, email)
```

- `backend/app/auth/base.py`：契约定义，包含 `Identity` 和 `AuthAdapter.identify()`。
- `backend/app/auth/demo.py`：内置 stub，使用 signed-cookie JWT 和预设用户。
- `backend/app/auth/prismax.py`：**PrismaX 需要填写的文件**。
- `backend/app/auth/deps.py`：FastAPI 依赖 `current_user` / `optional_user`，所有 router 都通过它们获取用户。它们会调用当前启用的 adapter，并把返回的 `Identity` 映射到本地 `users` 表，按 `external_id` 作为键。

用户的帖子、评论、点赞和收藏都使用 **内部** user id 关联。因此只要每个人的 `external_id` 稳定，从 demo 切换到 PrismaX 后，历史数据也可以保留下来。

### 使用 PrismaX 用户系统

设置 `AUTH_PROVIDER=prismax`，并让 `PrismaxAuthAdapter.identify()` 在请求已认证时返回一个 `Identity`。`prismax.py` 中已经草拟了两种常见路径：

**A. 验证 PrismaX 签发的 JWT**（默认骨架）。通过环境变量配置：

```bash
AUTH_PROVIDER=prismax
PRISMAX_TOKEN_SOURCE=bearer        # "bearer" header，或某个 cookie 名
PRISMAX_JWT_ALGORITHMS=RS256       # 或 HS256
PRISMAX_JWT_PUBLIC_KEY=<PEM>       # RS256 使用
PRISMAX_JWT_SECRET=<shared secret> # HS256 使用
PRISMAX_JWT_AUDIENCE=<aud>         # 可选
PRISMAX_JWT_ISSUER=<iss>           # 可选
PRISMAX_CLAIM_SUB=sub              # claim -> external_id
PRISMAX_CLAIM_NAME=name
PRISMAX_CLAIM_EMAIL=email
```

**B. 信任反向代理 header**（如果 PrismaX 在边缘层完成认证）。取消 `prismax.py` 中 header 示例代码的注释，读取如 `X-Auth-User-Id` / `X-Auth-User-Name`。

当 `AUTH_PROVIDER=prismax` 时，demo 的 `/api/auth/demo/*` 路由会自动返回 404，前端的 Sign-In modal 也可以移除，由 PrismaX 负责登录。

### 前端说明

登录弹窗和 `requireAuth()` 调用在 `frontend/app/providers.tsx` 中。接入 PrismaX 认证后，把弹窗触发改成跳转到 PrismaX 登录页即可；其他逻辑（`frontend/lib/api.ts` 中的 `credentials: "include"` fetch）可以保持不变。

---

## API 表面

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/api/health` | - | 存活检查 + 当前认证 provider |
| GET | `/api/auth/me` | - | 当前用户或 `null` |
| GET | `/api/auth/provider` | - | 当前 provider + 是否暴露登录路由 |
| POST | `/api/auth/logout` | - | 清除 session |
| GET | `/api/auth/demo/users` | demo | 预设身份列表 |
| POST | `/api/auth/demo/login` | demo | stub 登录，设置 cookie |
| GET | `/api/threads` | - | 列表（`category`, `sort`, `q`, `limit`, `offset`） |
| GET | `/api/threads/{id}` | - | 帖子详情 + blocks + viewer 状态 |
| POST | `/api/threads` | yes | 创建帖子（草稿或发布） |
| PATCH | `/api/threads/{id}` | yes（作者） | 更新帖子 |
| POST | `/api/threads/{id}/publish` | yes（作者） | 发布草稿 |
| DELETE | `/api/threads/{id}` | yes（作者） | 删除帖子 |
| GET | `/api/me/drafts` | yes | 我的草稿 |
| GET | `/api/me/saved` | yes | 我的收藏帖子 |
| POST | `/api/threads/{id}/like` | yes | 切换帖子点赞 |
| POST | `/api/threads/{id}/save` | yes | 切换收藏 |
| GET | `/api/threads/{id}/comments` | - | 嵌套评论 |
| POST | `/api/threads/{id}/comments` | yes | 添加评论 / 回复 |
| POST | `/api/comments/{id}/like` | yes | 切换评论点赞 |
| GET | `/api/categories` | - | 分类及数量 |

## 数据模型

`users` · `threads`（block 内容存为 JSON；`status` = draft/published）· `comments`（通过 `parent_id` 支持一层回复）· `likes`（thread/comment 多态目标）· `saves`。

Threads/comments 带有 `seed_*` baseline counts，因此从原型导入的数字（如 842 likes 等）可以继续展示，真实互动会在此基础上累加。

## 说明 / 生产后续事项

- 编辑器中的 block HTML 会通过 `dangerouslySetInnerHTML` 渲染。多租户生产使用前，需要增加服务端 sanitization（如 `bleach`）。
- 封面图 / 内联图片当前以内联 data URL 存储。规模化时应改为对象存储，并只保存 URL。
- 页面目前是 client-rendered（浏览器中 fetch）。如果需要 SEO，可以后续把列表页和文章页迁移为 server components，并转发 cookies 以获得 viewer state。
