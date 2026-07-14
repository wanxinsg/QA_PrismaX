"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import type { Comment, ThreadDetail } from "@/lib/types";
import { BlockRenderer } from "@/components/BlockRenderer";
import { ArrowLeftIcon, BookmarkIcon, ChatIcon, HeartIcon, ShareIcon } from "@/components/Icons";
import { fmt } from "@/components/ThreadCard";
import { useAuth, useToast } from "@/app/providers";

export default function ThreadPage() {
  const params = useParams<{ id: string }>();
  const id = Number(params.id);
  const router = useRouter();
  const { requireAuth } = useAuth();
  const toast = useToast();

  const [thread, setThread] = useState<ThreadDetail | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [notFound, setNotFound] = useState(false);
  const [mainText, setMainText] = useState("");
  const [replyOpen, setReplyOpen] = useState<number | null>(null);
  const [replyText, setReplyText] = useState("");
  const [likePulse, setLikePulse] = useState(false);
  const [added, setAdded] = useState(0); // comments/replies posted this session
  const pulseTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!id) return;
    api.getThread(id).then(setThread).catch((e) => {
      if (e instanceof ApiError && e.status === 404) setNotFound(true);
    });
    api.listComments(id).then(setComments).catch(() => {});
    window.scrollTo({ top: 0 });
  }, [id]);

  if (notFound) {
    return (
      <div style={{ textAlign: "center", padding: "120px 20px" }}>
        <p className="serif" style={{ fontStyle: "italic", fontSize: 30 }}>Thread not found.</p>
        <button onClick={() => router.push("/")} className="reset hover-accent" style={{ fontSize: 12, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", color: "var(--meta)", marginTop: 12 }}>Back to Discussion</button>
      </div>
    );
  }
  if (!thread) {
    return <div style={{ padding: "80px 20px", textAlign: "center", color: "var(--meta)" }}>Loading…</div>;
  }

  const totalContributions = thread.comment_count + added;

  async function toggleLike() {
    if (!requireAuth() || !thread) return;
    setLikePulse(true);
    if (pulseTimer.current) clearTimeout(pulseTimer.current);
    pulseTimer.current = setTimeout(() => setLikePulse(false), 360);
    try {
      const r = await api.likeThread(thread.id);
      setThread({ ...thread, liked: r.active, like_count: r.count });
    } catch {
      toast("Could not register like.");
    }
  }

  async function toggleSave() {
    if (!requireAuth() || !thread) return;
    try {
      const r = await api.saveThread(thread.id);
      setThread({ ...thread, saved: r.active });
      toast(r.active ? "Saved to your collection." : "Removed from saved.");
    } catch {
      toast("Could not save thread.");
    }
  }

  function share() {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(window.location.href).catch(() => {});
    }
    toast("Link copied to clipboard.");
  }

  async function postComment() {
    if (!requireAuth()) return;
    const body = mainText.trim();
    if (!body) return;
    try {
      const c = await api.postComment(id, { body });
      setComments((prev) => [c, ...prev]);
      setAdded((n) => n + 1);
      setMainText("");
      toast("Reply posted to the discourse.");
    } catch {
      toast("Could not post reply.");
    }
  }

  async function postReply(parentId: number) {
    if (!requireAuth()) return;
    const body = replyText.trim();
    if (!body) return;
    try {
      const r = await api.postComment(id, { body, parent_id: parentId });
      setComments((prev) => prev.map((c) => (c.id === parentId ? { ...c, replies: [...c.replies, r] } : c)));
      setAdded((n) => n + 1);
      setReplyText("");
      setReplyOpen(null);
      toast("Reply added.");
    } catch {
      toast("Could not add reply.");
    }
  }

  async function likeComment(commentId: number) {
    if (!requireAuth()) return;
    try {
      const res = await api.likeComment(commentId);
      setComments((prev) =>
        prev.map((c) =>
          c.id === commentId ? { ...c, liked: res.active, like_count: res.count } : c
        )
      );
    } catch {
      toast("Could not register like.");
    }
  }

  const accent = "var(--accent)";

  return (
    <div className="view-in">
      <article style={{ width: "100%", maxWidth: 760, margin: "0 auto", padding: "clamp(28px,5vw,52px) clamp(16px,5vw,28px) 40px" }}>
        <button onClick={() => router.push("/")} className="reset hover-accent" style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11, fontWeight: 700, letterSpacing: 1.2, textTransform: "uppercase", color: "var(--meta)", marginBottom: 34 }}>
          <ArrowLeftIcon size={15} /> Back to Discussion
        </button>

        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 18, fontSize: 10, fontWeight: 700, letterSpacing: 1.8, textTransform: "uppercase", color: accent }}>
          <ChatIcon size={14} /> Community / {thread.category}
        </div>

        <h1 className="serif" style={{ margin: 0, fontWeight: 300, fontStyle: "italic", fontSize: "clamp(38px,6vw,58px)", lineHeight: 1.04, letterSpacing: -1.5, color: "var(--ink)" }}>{thread.title}</h1>

        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16, margin: "38px 0 30px", paddingBottom: 26, borderBottom: "1px solid var(--line-soft)", flexWrap: "wrap" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 13 }}>
            <div className="serif" style={{ width: 42, height: 42, borderRadius: "50%", background: thread.author.avatar_color ? `linear-gradient(135deg, ${thread.author.avatar_color}, var(--accent2))` : "linear-gradient(135deg,#FDDAB2,#E3B27C)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18, color: "#fff" }}>{thread.author.name.charAt(0)}</div>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: "var(--ink)" }}>{thread.author.name}</div>
              <div style={{ fontSize: 11, color: "var(--meta)", marginTop: 2 }}>Published {thread.date} · {readingTime(thread)} min read</div>
            </div>
          </div>
          <button onClick={toggleSave} className="reset hover-accent" style={{ border: "1px solid var(--line)", borderRadius: 24, padding: "9px 16px", display: "flex", alignItems: "center", gap: 8, fontSize: 11, fontWeight: 700, letterSpacing: 0.8, textTransform: "uppercase", color: thread.saved ? accent : "var(--ink2)" }}>
            <BookmarkIcon size={13} fill={thread.saved ? accent : "none"} /> {thread.saved ? "Saved" : "Save"}
          </button>
        </div>

        <BlockRenderer blocks={thread.content} />

        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "18px 0", borderTop: "1px solid var(--line-soft)", borderBottom: "1px solid var(--line-soft)" }}>
          <button onClick={toggleLike} className="reset" style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 14, fontWeight: 600, color: thread.liked ? accent : "var(--ink2)", transition: "color .25s" }}>
            <span className={likePulse ? "heart-pop" : ""} style={{ display: "flex" }}><HeartIcon size={20} fill={thread.liked ? accent : "none"} /></span>
            {fmt(thread.like_count)}
          </button>
          <button onClick={share} className="reset hover-accent" style={{ display: "flex", alignItems: "center", gap: 9, fontSize: 13, fontWeight: 600, color: "var(--ink2)" }}>
            <ShareIcon size={17} /> Share
          </button>
        </div>

        <section style={{ marginTop: 48 }}>
          <h3 className="serif" style={{ margin: "0 0 22px", fontStyle: "italic", fontWeight: 400, fontSize: 26, color: "var(--ink)", display: "flex", alignItems: "baseline", gap: 12 }}>
            Discourse <span style={{ fontFamily: "var(--font-manrope)", fontStyle: "normal", fontSize: 12, fontWeight: 600, letterSpacing: 1, color: "var(--meta)" }}>{totalContributions} contributions</span>
          </h3>

          <div style={{ background: "var(--surface)", border: "1px solid var(--line-soft)", borderRadius: 8, padding: 18, marginBottom: 30, boxShadow: "var(--shadow)" }}>
            <textarea value={mainText} onChange={(e) => setMainText(e.target.value)} placeholder="Contribute to the monograph…" style={{ width: "100%", minHeight: 74, resize: "vertical", border: "none", outline: "none", background: "none", fontSize: 14, lineHeight: 1.6, color: "var(--ink)", display: "block" }} />
            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 10 }}>
              <button onClick={postComment} className="reset btn-dark" style={{ background: "var(--ink)", color: "#FAF9F6", fontSize: 11, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", padding: "10px 20px", borderRadius: 24 }}>Post Reply</button>
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 26 }}>
            {comments.map((c) => (
              <div key={c.id} className="fade-in" style={{ display: "flex", gap: 14 }}>
                <Avatar initials={c.author.initials} size={38} color={c.author.avatar_color} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
                    <span style={{ fontSize: 13, fontWeight: 700, color: "var(--ink)" }}>{c.author.name}</span>
                    <span style={{ fontSize: 10, fontWeight: 600, letterSpacing: 0.8, textTransform: "uppercase", color: "var(--meta)" }}>{c.time}</span>
                  </div>
                  <p style={{ margin: "7px 0 10px", fontSize: 14, lineHeight: 1.62, color: "var(--ink2)" }}>{c.body}</p>
                  <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
                    <button onClick={() => { setReplyOpen(replyOpen === c.id ? null : c.id); setReplyText(""); }} className="reset hover-accent" style={{ fontSize: 11, fontWeight: 700, letterSpacing: 0.6, color: "var(--meta)" }}>Reply</button>
                    <button onClick={() => likeComment(c.id)} className="reset" style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, fontWeight: 600, color: c.liked ? accent : "var(--meta)" }}>
                      <HeartIcon size={12} fill={c.liked ? accent : "none"} /> {c.like_count}
                    </button>
                  </div>

                  {replyOpen === c.id && (
                    <div className="fade-in" style={{ marginTop: 14, display: "flex", gap: 10, alignItems: "flex-start" }}>
                      <input autoFocus value={replyText} onChange={(e) => setReplyText(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") postReply(c.id); }} placeholder="Write a reply…" style={{ flex: 1, border: "1px solid var(--line-soft)", borderRadius: 8, padding: "10px 12px", outline: "none", fontSize: 13, color: "var(--ink)", background: "var(--surface)" }} />
                      <button onClick={() => postReply(c.id)} className="reset btn-dark" style={{ background: "var(--ink)", color: "#FAF9F6", fontSize: 11, fontWeight: 700, letterSpacing: 0.8, textTransform: "uppercase", padding: "11px 16px", borderRadius: 8, flexShrink: 0 }}>Send</button>
                    </div>
                  )}

                  {c.replies.length > 0 && (
                    <div style={{ marginTop: 18, paddingLeft: 18, borderLeft: "1px solid var(--line-soft)", display: "flex", flexDirection: "column", gap: 18 }}>
                      {c.replies.map((r) => (
                        <div key={r.id} className="fade-in" style={{ display: "flex", gap: 12 }}>
                          <Avatar initials={r.author.initials} size={32} color={r.author.avatar_color} />
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <div style={{ display: "flex", alignItems: "baseline", gap: 9 }}>
                              <span style={{ fontSize: 12, fontWeight: 700, color: "var(--ink)" }}>{r.author.name}</span>
                              <span style={{ fontSize: 10, fontWeight: 600, letterSpacing: 0.8, textTransform: "uppercase", color: "var(--meta)" }}>{r.time}</span>
                            </div>
                            <p style={{ margin: "6px 0 0", fontSize: 13, lineHeight: 1.6, color: "var(--ink2)" }}>{r.body}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      </article>
    </div>
  );
}

function Avatar({ initials, size, color }: { initials: string; size: number; color?: string | null }) {
  return (
    <div style={{ flexShrink: 0, width: size, height: size, borderRadius: "50%", background: color || "var(--surface2)", border: "1px solid var(--line-soft)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: size > 34 ? 11 : 10, fontWeight: 700, letterSpacing: 0.5, color: color ? "#fff" : "var(--meta)" }}>
      {initials}
    </div>
  );
}

function readingTime(t: ThreadDetail): number {
  const words = (t.content || []).reduce((n, b) => n + (b.text ? b.text.trim().split(/\s+/).length : 0), 0);
  return Math.max(1, Math.round(words / 200));
}
