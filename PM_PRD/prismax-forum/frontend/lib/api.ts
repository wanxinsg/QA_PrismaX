import type {
  Category,
  Comment,
  PresetUser,
  ThreadDetail,
  ThreadList,
  ToggleResult,
  User,
} from "./types";

export interface ThreadCreate {
  title: string;
  category: string;
  excerpt?: string;
  cover_image?: string | null;
  content: { type: string; html?: string; text?: string; caption?: string; src?: string | null }[];
  status: "draft" | "published";
}

/**
 * Base URL for API calls. Empty by default → calls go to this origin's `/api/*`,
 * which Next.js rewrites (see next.config.ts) proxy to the FastAPI backend. This
 * keeps everything same-origin: no CORS, no cross-origin cookies, works behind any
 * host or proxy. Override with NEXT_PUBLIC_API_BASE only for split deployments
 * where the API is on a different origin.
 */
function apiBase(): string {
  return process.env.NEXT_PUBLIC_API_BASE || "";
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${apiBase()}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  // --- auth ---
  me: () => request<User | null>("/api/auth/me"),
  provider: () => request<{ provider: string; login_routes: boolean }>("/api/auth/provider"),
  demoUsers: () => request<PresetUser[]>("/api/auth/demo/users"),
  demoLogin: (payload: { external_id?: string; name?: string }) =>
    request<User>("/api/auth/demo/login", { method: "POST", body: JSON.stringify(payload) }),
  logout: () => request<{ detail: string }>("/api/auth/logout", { method: "POST" }),

  // --- threads ---
  listThreads: (params: {
    category?: string;
    sort?: string;
    q?: string;
    limit?: number;
    offset?: number;
  }) => {
    const qs = new URLSearchParams();
    if (params.category) qs.set("category", params.category);
    if (params.sort) qs.set("sort", params.sort);
    if (params.q) qs.set("q", params.q);
    if (params.limit != null) qs.set("limit", String(params.limit));
    if (params.offset != null) qs.set("offset", String(params.offset));
    return request<ThreadList>(`/api/threads?${qs.toString()}`);
  },
  getThread: (id: number) => request<ThreadDetail>(`/api/threads/${id}`),
  createThread: (payload: ThreadCreate) =>
    request<ThreadDetail>("/api/threads", { method: "POST", body: JSON.stringify(payload) }),
  updateThread: (id: number, payload: Partial<ThreadCreate>) =>
    request<ThreadDetail>(`/api/threads/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteThread: (id: number) =>
    request<{ detail: string }>(`/api/threads/${id}`, { method: "DELETE" }),
  myDrafts: () => request<ThreadDetail[]>("/api/me/drafts"),
  mySaved: () => request<ThreadDetail[]>("/api/me/saved"),
  likeThread: (id: number) =>
    request<ToggleResult>(`/api/threads/${id}/like`, { method: "POST" }),
  saveThread: (id: number) =>
    request<ToggleResult>(`/api/threads/${id}/save`, { method: "POST" }),

  // --- comments ---
  listComments: (threadId: number) =>
    request<Comment[]>(`/api/threads/${threadId}/comments`),
  postComment: (threadId: number, payload: { body: string; parent_id?: number }) =>
    request<Comment>(`/api/threads/${threadId}/comments`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  likeComment: (id: number) =>
    request<ToggleResult>(`/api/comments/${id}/like`, { method: "POST" }),

  // --- categories ---
  categories: () => request<Category[]>("/api/categories"),
};
