"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ThreadCard as ThreadCardT } from "@/lib/types";
import { ThreadCard } from "@/components/ThreadCard";
import { useAuth, useToast } from "@/app/providers";

export default function SavedPage() {
  const { user, loading: authLoading, requireAuth } = useAuth();
  const toast = useToast();
  const [items, setItems] = useState<ThreadCardT[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    api.mySaved().then(setItems).catch(() => setItems([])).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      requireAuth();
      setLoading(false);
      return;
    }
    load();
  }, [authLoading, user, requireAuth, load]);

  function patch(id: number, changes: Partial<ThreadCardT>) {
    setItems((prev) => prev.map((t) => (t.id === id ? { ...t, ...changes } : t)));
  }
  async function onLike(id: number) {
    try {
      const r = await api.likeThread(id);
      patch(id, { liked: r.active, like_count: r.count });
    } catch {
      toast("Could not register like.");
    }
  }
  async function onSave(id: number) {
    try {
      const r = await api.saveThread(id);
      if (!r.active) setItems((prev) => prev.filter((t) => t.id !== id));
      toast("Removed from saved.");
    } catch {
      toast("Could not update.");
    }
  }

  return (
    <div className="view-in" style={{ width: "100%", maxWidth: 1240, margin: "0 auto", padding: "clamp(28px,5vw,52px) clamp(16px,4vw,28px) 60px" }}>
      <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: 1.8, textTransform: "uppercase", color: "var(--accent)" }}>Your Workspace</div>
      <h1 className="serif" style={{ margin: "8px 0 30px", fontWeight: 300, fontStyle: "italic", fontSize: "clamp(38px,6vw,52px)", letterSpacing: -1.5, color: "var(--ink)" }}>Saved</h1>

      {loading ? (
        <p style={{ color: "var(--meta)" }}>Loading…</p>
      ) : items.length === 0 ? (
        <p className="serif" style={{ fontStyle: "italic", fontSize: 22, color: "var(--meta)" }}>Nothing saved yet. Tap the bookmark on any thread to keep it here.</p>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(min(100%,330px),1fr))", gap: 24 }}>
          {items.map((t) => (
            <ThreadCard key={t.id} thread={t} onLike={onLike} onSave={onSave} />
          ))}
        </div>
      )}
    </div>
  );
}
