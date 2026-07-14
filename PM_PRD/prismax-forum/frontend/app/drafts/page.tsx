"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { ThreadDetail } from "@/lib/types";
import { useAuth, useToast } from "@/app/providers";

export default function DraftsPage() {
  const router = useRouter();
  const { user, loading: authLoading, requireAuth } = useAuth();
  const toast = useToast();
  const [drafts, setDrafts] = useState<ThreadDetail[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    api.myDrafts().then(setDrafts).catch(() => setDrafts([])).finally(() => setLoading(false));
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

  async function publish(id: number) {
    try {
      await api.updateThread(id, { status: "published" });
      toast("Draft published.");
      load();
    } catch {
      toast("Could not publish.");
    }
  }
  async function remove(id: number) {
    try {
      await api.deleteThread(id);
      setDrafts((prev) => prev.filter((d) => d.id !== id));
      toast("Draft deleted.");
    } catch {
      toast("Could not delete.");
    }
  }

  return (
    <div className="view-in" style={{ width: "100%", maxWidth: 760, margin: "0 auto", padding: "clamp(28px,5vw,52px) clamp(16px,5vw,28px) 60px" }}>
      <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: 1.8, textTransform: "uppercase", color: "var(--accent)" }}>Your Workspace</div>
      <h1 className="serif" style={{ margin: "8px 0 30px", fontWeight: 300, fontStyle: "italic", fontSize: "clamp(38px,6vw,52px)", letterSpacing: -1.5, color: "var(--ink)" }}>Drafts</h1>

      {loading ? (
        <p style={{ color: "var(--meta)" }}>Loading…</p>
      ) : drafts.length === 0 ? (
        <p className="serif" style={{ fontStyle: "italic", fontSize: 22, color: "var(--meta)" }}>No drafts yet. Start a new monograph from “New Post”.</p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {drafts.map((d) => (
            <div key={d.id} style={{ background: "var(--surface)", border: "1px solid var(--line-soft)", borderRadius: 8, padding: 20, boxShadow: "var(--shadow)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 10, fontWeight: 700, letterSpacing: 1.2, textTransform: "uppercase", color: "var(--meta)", marginBottom: 8 }}>
                <span style={{ color: "var(--accent)" }}>{d.category}</span> · <span>Updated {d.date}</span>
              </div>
              <h2 className="serif" style={{ margin: "0 0 8px", fontWeight: 500, fontSize: 22, color: "var(--ink)" }}>{d.title || "Untitled draft"}</h2>
              <p style={{ margin: "0 0 16px", fontSize: 13.5, lineHeight: 1.6, color: "var(--ink2)" }}>{d.excerpt}</p>
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                <button onClick={() => router.push(`/compose?id=${d.id}`)} className="reset btn-dark" style={{ background: "var(--ink)", color: "#FAF9F6", fontSize: 11, fontWeight: 700, letterSpacing: 0.8, textTransform: "uppercase", padding: "9px 16px", borderRadius: 22 }}>Edit</button>
                <button onClick={() => publish(d.id)} className="reset btn-outline" style={{ border: "1px solid var(--line)", borderRadius: 22, padding: "9px 16px", fontSize: 11, fontWeight: 700, letterSpacing: 0.8, textTransform: "uppercase", color: "var(--ink2)" }}>Publish</button>
                <button onClick={() => remove(d.id)} className="reset btn-outline" style={{ border: "1px solid var(--line)", borderRadius: 22, padding: "9px 16px", fontSize: 11, fontWeight: 700, letterSpacing: 0.8, textTransform: "uppercase", color: "var(--ink2)" }}>Delete</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
