# Prisma(x) Forum

A community discussion / "Digital Monograph" forum — a production rebuild of the
`Prisma Discussion` design prototype.

- **Backend**: FastAPI + SQLite (SQLAlchemy), port **8085**
- **Frontend**: Next.js (App Router, TypeScript), port **3001**
- **Auth**: a **pluggable adapter** — a self-contained demo login for now, with a
  drop-in seam for PrismaX's own user system (see [Auth integration](#auth-integration)).

The browser only ever talks to the web origin (`:3001`); the Next server proxies
`/api/*` to the backend (see `frontend/next.config.ts`). So there is **no CORS and
no cross-origin cookie** to worry about, and it works behind any host or proxy. The
API binds to loopback in production — it is not exposed publicly.

```
prismax-forum/
├── backend/    FastAPI app, SQLite db, seed script
└── frontend/   Next.js app (faithful port of the prototype UI)
```

## Features

Browse threads (category filter, Latest / Most Discussed sort, search, pagination) ·
read articles with block content (headings, quotes, bullets, code, images) ·
like & save · threaded comments and replies · a block-based editor with cover
images, drafts and publishing.

---

## Run it

### 1. Backend (port 8085)

```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # first time
cp .env.example .env                # optional; defaults work for local demo
.venv/bin/python -m app.seed        # load the prototype's content (idempotent)
./run.sh                            # uvicorn on 0.0.0.0:8085
```

Health check: `curl localhost:8085/api/health`
Interactive API docs: `http://localhost:8085/docs`

### 2. Frontend (port 3001)

```bash
cd frontend
npm install        # first time
npm run dev        # dev server on 0.0.0.0:3001
# or: npm run build && npm start   # production
```

Open `http://localhost:3001` (or `http://34.186.168.140:3001` from outside the VM —
ports 3000–9000 are open).

> The frontend calls `/api/*` on its own origin; Next proxies that to the backend
> (`BACKEND_ORIGIN`, default `http://localhost:8085`). For a split deployment where
> the API lives on a different origin, set `NEXT_PUBLIC_API_BASE` instead.

### Production on this VM (systemd, already running)

Both run as **systemd user units** (the convention other services here use), so they
survive logout/reboot. The web is public on `:3001`; the API is loopback-only.

```bash
export XDG_RUNTIME_DIR=/run/user/$(id -u)   # needed in a non-login shell
systemctl --user status  prismax-forum-{api,web}
systemctl --user restart prismax-forum-{api,web}
journalctl --user -u prismax-forum-web -f   # or tail /mnt/data/home/alex/logs/prismax-forum-*.log
```

After changing frontend code, rebuild before restarting the web unit:
`cd frontend && npm run build && systemctl --user restart prismax-forum-web`.

### Demo login

Click **Sign In** and pick a preset persona (You, Dr. Thorne, …) or type any name.
This is a **stub** — see below for replacing it with PrismaX's real auth.

---

## Auth integration

> **This is the part PrismaX cares about.** The forum never builds its own user
> system. All identity flows through one interface, selected by the
> `AUTH_PROVIDER` env var. Swapping providers changes **zero** forum/business code.

### How it's wired

```
request ─▶ AuthAdapter.identify(request) ─▶ Identity ─▶ upsert local users row ─▶ User
            (demo | prismax)                (external_id, name, email)
```

- `backend/app/auth/base.py` — the contract: `Identity` + `AuthAdapter.identify()`.
- `backend/app/auth/demo.py` — built-in stub (signed-cookie JWT, preset users).
- `backend/app/auth/prismax.py` — **the file PrismaX fills in**.
- `backend/app/auth/deps.py` — `current_user` / `optional_user` FastAPI deps that
  every router depends on. They call the active adapter and map the returned
  `Identity` onto a local `users` row keyed by `external_id`.

A user's threads, comments, likes and saves are all keyed on the **internal** user
id, so as long as `external_id` is stable per person, history survives the switch
from demo to PrismaX.

### To use PrismaX's user system

Set `AUTH_PROVIDER=prismax` and make `PrismaxAuthAdapter.identify()` return an
`Identity` for an authenticated request. Two common paths, both already sketched in
`prismax.py`:

**A. Verify a PrismaX-issued JWT** (default skeleton). Configure via env:

```bash
AUTH_PROVIDER=prismax
PRISMAX_TOKEN_SOURCE=bearer        # "bearer" header, or the name of a cookie
PRISMAX_JWT_ALGORITHMS=RS256       # or HS256
PRISMAX_JWT_PUBLIC_KEY=<PEM>       # RS256 …
PRISMAX_JWT_SECRET=<shared secret> # … or HS256
PRISMAX_JWT_AUDIENCE=<aud>         # optional
PRISMAX_JWT_ISSUER=<iss>           # optional
PRISMAX_CLAIM_SUB=sub              # claim → external_id
PRISMAX_CLAIM_NAME=name
PRISMAX_CLAIM_EMAIL=email
```

**B. Trust a reverse-proxy header** (if PrismaX authenticates at the edge). Uncomment
the header block in `prismax.py` and read e.g. `X-Auth-User-Id` / `X-Auth-User-Name`.

When `AUTH_PROVIDER=prismax`, the demo `/api/auth/demo/*` routes return 404
automatically and the frontend's Sign-In modal can be removed (PrismaX owns login).

### Frontend note

The login modal and `requireAuth()` calls live in `frontend/app/providers.tsx`.
With PrismaX auth, replace the modal trigger with a redirect to PrismaX's login;
everything else (the `credentials: "include"` fetches in `frontend/lib/api.ts`)
stays the same.

---

## API surface

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/api/health` | – | liveness + active auth provider |
| GET | `/api/auth/me` | – | current user or `null` |
| GET | `/api/auth/provider` | – | active provider + whether it exposes login routes |
| POST | `/api/auth/logout` | – | clear session |
| GET | `/api/auth/demo/users` | demo | preset personas |
| POST | `/api/auth/demo/login` | demo | stub login → sets cookie |
| GET | `/api/threads` | – | list (`category`, `sort`, `q`, `limit`, `offset`) |
| GET | `/api/threads/{id}` | – | thread detail + blocks + viewer state |
| POST | `/api/threads` | ✓ | create (draft or published) |
| PATCH | `/api/threads/{id}` | ✓ (author) | update |
| POST | `/api/threads/{id}/publish` | ✓ (author) | publish a draft |
| DELETE | `/api/threads/{id}` | ✓ (author) | delete |
| GET | `/api/me/drafts` | ✓ | my drafts |
| GET | `/api/me/saved` | ✓ | my saved threads |
| POST | `/api/threads/{id}/like` | ✓ | toggle like |
| POST | `/api/threads/{id}/save` | ✓ | toggle save |
| GET | `/api/threads/{id}/comments` | – | nested comments |
| POST | `/api/threads/{id}/comments` | ✓ | add comment / reply |
| POST | `/api/comments/{id}/like` | ✓ | toggle comment like |
| GET | `/api/categories` | – | categories with counts |

## Data model

`users` · `threads` (block content as JSON; `status` = draft/published) ·
`comments` (one level of replies via `parent_id`) · `likes` (polymorphic on
thread/comment) · `saves`. Threads/comments carry `seed_*` baseline counts so the
imported prototype numbers (842 likes, etc.) display while real interactions add on
top.

## Notes / production follow-ups

- Block HTML from the editor is rendered with `dangerouslySetInnerHTML`. Add
  server-side sanitization (e.g. `bleach`) before multi-tenant production use.
- Cover/inline images are stored inline as data URLs. For scale, swap to object
  storage and store URLs instead.
- Pages are client-rendered (fetch in the browser). For SEO, the list and article
  pages can be moved to server components later (forward cookies for viewer state).
