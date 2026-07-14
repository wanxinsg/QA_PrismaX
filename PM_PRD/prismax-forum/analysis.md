# Prismax Forum 逻辑分析

`prismax-forum/` 是一个独立的论坛应用：后端 FastAPI 提供论坛 API，前端 Next.js 渲染 UI，并通过 Next rewrite 把浏览器的 `/api/*` 请求代理到后端。

## 整体结构

- `README.md`：项目定位、运行方式、认证集成、API 和数据模型说明。
- `backend/app/main.py`：FastAPI 入口，启动时初始化数据库，并挂载 `auth`、`threads`、`comments`、`categories` 路由。
- `frontend/app/page.tsx`：首页帖子列表。
- `frontend/lib/api.ts`：前端所有接口调用的薄封装。

## 核心业务流

用户打开首页后，前端调用：

```text
/api/categories
/api/threads?category=...&sort=...&q=...
```

后端在 `backend/app/routers/threads.py` 查询 `published` 状态的帖子，支持分类、搜索、排序和分页，然后通过 `backend/app/serializers.py` 计算点赞数、评论数，以及当前用户是否已经 liked/saved。

点击帖子卡片后进入：

```text
/thread/[id]
```

对应前端页面是 `frontend/app/thread/[id]/page.tsx`，它会请求：

```text
/api/threads/{id}
/api/threads/{id}/comments
```

正文由 `frontend/components/BlockRenderer.tsx` 渲染。评论支持一层嵌套回复；后端会把“回复的回复”折回到顶层评论下面，避免无限层级。

## 数据模型

主要 ORM 在 `backend/app/models.py`：

```text
User
Thread
Comment
Like
Save
```

`Thread.content` 是 JSON block 列表，比如段落、标题、引用、代码、图片等。

`Like` 是多态表，通过 `target_type = thread|comment` 区分点赞对象。

`Save` 单独记录用户收藏帖子。

有一个小设计点：`Thread` 和 `Comment` 都有 `seed_likes` / `seed_comments`，用于保留原型导入时的展示数量，真实互动是在这个基础上累加。

## 发帖和草稿逻辑

发帖入口是 `frontend/app/compose/page.tsx`。

编辑器是 block-based：

```text
title
category
cover_image
content: [{ type, html, text, caption, src }]
status: draft | published
```

保存草稿或发布调用：

```text
POST /api/threads
PATCH /api/threads/{id}
```

草稿列表在 `frontend/app/drafts/page.tsx`，只显示当前用户自己的 `draft`。发布草稿本质上是把 `status` 更新为 `published`。

## 登录和身份逻辑

这是这个项目最重要的集成点。它没有自己完整的用户系统，而是抽象了一个 auth adapter。

相关文件：

- `backend/app/auth/deps.py`
- `backend/app/auth/__init__.py`
- `backend/app/auth/demo.py`
- `backend/app/auth/prismax.py`

调用链是：

```text
请求进来
  -> current_user / optional_user
  -> get_adapter().identify(request)
  -> 得到 Identity(external_id, name, email)
  -> upsert 到本地 users 表
  -> 业务逻辑使用内部 User.id
```

默认 `AUTH_PROVIDER=demo`，登录弹窗会发 demo JWT cookie。切到 `AUTH_PROVIDER=prismax` 后，`PrismaxAuthAdapter` 可以从 Bearer token 或 cookie 中验证 PrismaX 的 JWT。论坛业务代码不需要改。

前端登录状态在 `frontend/app/providers.tsx`，启动时请求 `/api/auth/me`，需要登录的动作统一走 `requireAuth()`。

## 前后端连接方式

`frontend/next.config.ts` 做了 rewrite：

```text
浏览器请求 /api/*
Next.js 代理到 http://localhost:8085/api/*
```

因此浏览器只面对前端同源地址，cookie 也保持同源，可以减少 CORS 和跨域 cookie 问题。

## 风险点

1. `BlockRenderer.tsx` 使用 `dangerouslySetInnerHTML` 渲染编辑器内容，目前没有看到服务端 HTML sanitization，多用户生产环境有 XSS 风险。
2. 图片以 base64 data URL 存在 `cover_image` / block `src` 中，小规模 demo 可以，正式环境建议换对象存储。
3. 后端现在用 `Base.metadata.create_all()` 自动建表，没有迁移系统，后续字段演进建议加 Alembic。
4. 列表序列化每个帖子分别查点赞数、评论数、收藏状态，数据量上来后会有 N+1 查询问题。

## 总结

这是一个完成度较高的独立论坛模块，业务边界很清楚，尤其 auth adapter 设计适合接入 PrismaX 主系统。当前更像 demo / 原型产品化版本，真正上线前重点补安全清洗、图片存储、数据库迁移和查询性能。
