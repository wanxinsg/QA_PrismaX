"use client";

import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import type { Category, ThreadCard as ThreadCardT } from "@/lib/types";
import { ThreadCard } from "@/components/ThreadCard";
import { ChatIcon } from "@/components/Icons";
import { useAuth, useToast } from "./providers";

const PAGE = 12;

function ListView() {
  const searchParams = useSearchParams();
  const q = searchParams.get("q") || "";
  const { requireAuth } = useAuth();
  const toast = useToast();

  const [categories, setCategories] = useState<Category[]>([{ label: "All", count: 0 }]);
  const [category, setCategory] = useState("All");
  const [sort, setSort] = useState<"latest" | "discussed">("latest");
  const [threads, setThreads] = useState<ThreadCardT[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [pulseId, setPulseId] = useState<number | null>(null);
  const pulseTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    api.categories().then(setCategories).catch(() => {});
  }, []);

  const fetchPage = useCallback(
    async (offset: number, replace: boolean) => {
      if (replace) setLoading(true);
      try {
        const data = await api.listThreads({ category, sort, q, limit: PAGE, offset });
        setTotal(data.total);
        setThreads((prev) => (replace ? data.items : [...prev, ...data.items]));
      } finally {
        if (replace) setLoading(false);
      }
    },
    [category, sort, q]
  );

  useEffect(() => {
    fetchPage(0, true);
  }, [fetchPage]);

  function patch(id: number, changes: Partial<ThreadCardT>) {
    setThreads((prev) => prev.map((t) => (t.id === id ? { ...t, ...changes } : t)));
  }

  async function onLike(id: number) {
    if (!requireAuth()) return;
    setPulseId(id);
    if (pulseTimer.current) clearTimeout(pulseTimer.current);
    pulseTimer.current = setTimeout(() => setPulseId(null), 360);
    try {
      const r = await api.likeThread(id);
      patch(id, { liked: r.active, like_count: r.count });
    } catch {
      toast("Could not register like.");
    }
  }

  async function onSave(id: number) {
    if (!requireAuth()) return;
    try {
      const r = await api.saveThread(id);
      patch(id, { saved: r.active });
      toast(r.active ? "Saved to your collection." : "Removed from saved.");
    } catch {
      toast("Could not save thread.");
    }
  }

  const filtering = q !== "" || category !== "All";
  const resultLabel = filtering ? `${threads.length} of ${total} threads` : `${total} threads`;
  const canLoadMore = threads.length < total;

  const tabBase: React.CSSProperties = {
    whiteSpace: "nowrap",
    fontSize: 12,
    fontWeight: 600,
    letterSpacing: 0.3,
    padding: "8px 16px",
    borderRadius: 30,
    transition: "all .25s",
    border: "1px solid transparent",
  };
  const segBase: React.CSSProperties = {
    whiteSpace: "nowrap",
    fontSize: 11,
    fontWeight: 700,
    letterSpacing: 0.8,
    padding: "8px 16px",
    borderRadius: 24,
    transition: "all .25s",
  };

  return (
    <div className="view-in">
      <section style={{ background: "linear-gradient(180deg,#F4F3F1 0%,var(--bg) 100%)", borderBottom: "1px solid var(--line-soft)" }}>
        <div style={{ width: "100%", maxWidth: 1240, margin: "0 auto", padding: "clamp(40px,7vw,80px) clamp(16px,4vw,28px) clamp(28px,4vw,40px)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 11, marginBottom: 14 }}>
            <span style={{ color: "var(--accent)", display: "flex" }}><ChatIcon size={15} /></span>
            <span style={{ fontWeight: 700, fontSize: 10, letterSpacing: 2.4, textTransform: "uppercase", color: "var(--accent)" }}>Community Monograph</span>
          </div>
          <h1 className="serif" style={{ margin: 0, fontWeight: 300, fontStyle: "italic", fontSize: "clamp(52px,9vw,84px)", lineHeight: 0.95, letterSpacing: -3, color: "var(--ink2)" }}>Discussion</h1>
          <p style={{ margin: "20px 0 0", maxWidth: 540, fontSize: 15, lineHeight: 1.65, color: "var(--ink2)", opacity: 0.85 }}>
            Exploring the intersection of robotics, ethics, and digital architecture. Peer-reviewed threads from our global community.
          </p>
        </div>
      </section>

      <div style={{ width: "100%", maxWidth: 1240, margin: "0 auto", padding: "clamp(20px,3.5vw,32px) clamp(16px,4vw,28px) 0" }}>
        <div style={{ display: "flex", gap: 8, overflowX: "auto", paddingBottom: 4 }}>
          {categories.map((c) => {
            const on = c.label === category;
            return (
              <button
                key={c.label}
                onClick={() => setCategory(c.label)}
                className="reset"
                style={{ ...tabBase, ...(on ? { background: "var(--ink)", color: "#FAF9F6" } : { background: "var(--surface)", color: "var(--ink2)", borderColor: "var(--line-soft)" }) }}
              >
                {c.label}
              </button>
            );
          })}
        </div>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16, flexWrap: "wrap", marginTop: 16 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, background: "var(--surface)", border: "1px solid var(--line-soft)", borderRadius: 30, padding: 4 }}>
            <button onClick={() => setSort("latest")} className="reset" style={{ ...segBase, ...(sort === "latest" ? { background: "var(--ink)", color: "#FAF9F6" } : { color: "var(--meta)" }) }}>Latest</button>
            <button onClick={() => setSort("discussed")} className="reset" style={{ ...segBase, ...(sort === "discussed" ? { background: "var(--ink)", color: "#FAF9F6" } : { color: "var(--meta)" }) }}>Most Discussed</button>
          </div>
          <span style={{ fontSize: 11, fontWeight: 600, letterSpacing: 1.4, textTransform: "uppercase", color: "var(--meta)" }}>{resultLabel}</span>
        </div>
      </div>

      <div style={{ width: "100%", maxWidth: 1240, margin: "0 auto", padding: "24px clamp(16px,4vw,28px) clamp(48px,7vw,72px)" }}>
        {loading ? (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(min(100%,330px),1fr))", gap: 24 }}>
            {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} />)}
          </div>
        ) : threads.length > 0 ? (
          <>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(min(100%,330px),1fr))", gap: 24 }}>
              {threads.map((t) => (
                <ThreadCard key={t.id} thread={t} pulse={pulseId === t.id} onLike={onLike} onSave={onSave} />
              ))}
            </div>
            <div style={{ display: "flex", justifyContent: "center", marginTop: 48 }}>
              <button
                onClick={() => (canLoadMore ? fetchPage(threads.length, false) : toast("You're all caught up — every thread is shown."))}
                className="reset btn-outline"
                style={{ border: "1px solid var(--line)", borderRadius: 30, padding: "13px 30px", fontSize: 11, fontWeight: 700, letterSpacing: 1.4, textTransform: "uppercase", color: "var(--ink2)" }}
              >
                Load More Threads
              </button>
            </div>
          </>
        ) : (
          <div style={{ textAlign: "center", padding: "clamp(56px,10vw,96px) 20px" }}>
            <div style={{ width: 64, height: 64, margin: "0 auto 22px", borderRadius: "50%", background: "var(--surface)", border: "1px solid var(--line-soft)", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--accent)" }}>
              <ChatIcon size={26} />
            </div>
            <p className="serif" style={{ fontStyle: "italic", fontSize: 30, color: "var(--ink)", margin: 0 }}>{q ? "No threads found." : "Nothing here yet."}</p>
            <p style={{ fontSize: 13, color: "var(--meta)", margin: "12px 0 22px" }}>{q ? "Try a different search term or category." : "No threads in this category — try another filter."}</p>
            <button onClick={() => setCategory("All")} className="reset btn-outline" style={{ border: "1px solid var(--line)", borderRadius: 26, padding: "11px 22px", fontSize: 11, fontWeight: 700, letterSpacing: 1.2, textTransform: "uppercase", color: "var(--ink2)" }}>Clear filters</button>
          </div>
        )}
      </div>
    </div>
  );
}

function Skeleton() {
  const bar = (w: string, h: number, light = false): React.CSSProperties => ({
    width: w,
    height: h,
    borderRadius: 4,
    background: light
      ? "linear-gradient(90deg,#F2F1EE 25%,#E8E6E2 37%,#F2F1EE 63%)"
      : "linear-gradient(90deg,#EFEEEB 25%,#E4E2DE 37%,#EFEEEB 63%)",
    backgroundSize: "600px 100%",
    animation: "shimmer 1.5s infinite linear",
  });
  return (
    <div style={{ minHeight: 312, background: "var(--surface)", border: "1px solid var(--line-soft)", borderRadius: 7, padding: 22, display: "flex", flexDirection: "column", gap: 14 }}>
      <div style={bar("88px", 11)} />
      <div style={bar("100%", 20)} />
      <div style={bar("70%", 20)} />
      <div style={{ ...bar("100%", 11, true), marginTop: 8 }} />
      <div style={bar("92%", 11, true)} />
      <div style={{ flex: 1 }} />
      <div style={{ paddingTop: 14, borderTop: "1px solid var(--line-soft)", display: "flex", gap: 12 }}>
        <div style={bar("44px", 12, true)} />
        <div style={bar("44px", 12, true)} />
      </div>
    </div>
  );
}

export default function HomePage() {
  return (
    <Suspense fallback={null}>
      <ListView />
    </Suspense>
  );
}
