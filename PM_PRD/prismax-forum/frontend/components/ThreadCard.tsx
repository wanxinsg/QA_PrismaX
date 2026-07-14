"use client";

import { useRouter } from "next/navigation";
import type { ThreadCard as ThreadCardT } from "@/lib/types";
import { ChatIcon, HeartIcon, BookmarkIcon } from "./Icons";

function fmt(n: number): string {
  return n >= 1000 ? `${(n / 1000).toFixed(1).replace(/\.0$/, "")}k` : `${n}`;
}

interface Props {
  thread: ThreadCardT;
  pulse?: boolean;
  onLike: (id: number) => void;
  onSave: (id: number) => void;
}

export function ThreadCard({ thread: t, pulse, onLike, onSave }: Props) {
  const router = useRouter();
  const accent = "var(--accent)";
  const meta = "var(--meta)";
  const ink2 = "var(--ink2)";

  return (
    <article
      onClick={() => router.push(`/thread/${t.id}`)}
      className="lift"
      style={{
        position: "relative",
        display: "flex",
        flexDirection: "column",
        minHeight: 312,
        background: t.badge ? "var(--surface2)" : "var(--surface)",
        border: "1px solid var(--line-soft)",
        borderRadius: 7,
        padding: 22,
        boxShadow: "var(--shadow)",
        cursor: "pointer",
        overflow: "hidden",
      }}
    >
      <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 11 }}>
        {t.badge ? (
          <span style={{ alignSelf: "flex-start", background: "rgba(140,115,85,0.1)", color: accent, fontWeight: 700, fontSize: 9, letterSpacing: 1.2, textTransform: "uppercase", padding: "4px 9px", borderRadius: 20 }}>
            {t.badge}
          </span>
        ) : (
          <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 10, fontWeight: 700, letterSpacing: 1.4, textTransform: "uppercase" }}>
            <span style={{ color: t.accent ? accent : meta }}>{t.accent ? "Featured" : t.author.name}</span>
            <span style={{ color: "var(--line)", fontWeight: 400 }}>•</span>
            <span style={{ color: meta, fontWeight: 500 }}>{t.date}</span>
          </div>
        )}
        <h2 className="serif" style={{ margin: 0, fontWeight: 500, fontSize: 21, lineHeight: 1.22, letterSpacing: -0.2, color: "var(--ink)" }}>
          {t.title}
        </h2>
        {t.cover_image && (
          <div style={{ position: "relative", height: 92, borderRadius: 4, overflow: "hidden", background: "#E3E2E0" }}>
            <div style={{ position: "absolute", inset: 0, backgroundImage: `url('${t.cover_image}')`, backgroundSize: "cover", backgroundPosition: "center", opacity: 0.62, mixBlendMode: "multiply" }} />
          </div>
        )}
        <p style={{ margin: 0, fontSize: 13, lineHeight: 1.62, color: ink2, display: "-webkit-box", WebkitLineClamp: 3, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
          {t.excerpt}
        </p>
      </div>

      <div style={{ marginTop: 16, paddingTop: 14, borderTop: "1px solid var(--line-soft)", display: "flex", alignItems: "center", gap: 16 }}>
        <span style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, fontWeight: 600, color: ink2 }}>
          <ChatIcon size={13} />
          {fmt(t.comment_count)}
        </span>
        <button
          onClick={(e) => { e.stopPropagation(); onLike(t.id); }}
          aria-label="Like"
          className="reset"
          style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, fontWeight: 600, color: t.liked ? accent : ink2, transition: "color .25s" }}
        >
          <span className={pulse ? "heart-pop" : ""} style={{ display: "flex" }}>
            <HeartIcon size={13} fill={t.liked ? accent : "none"} />
          </span>
          {fmt(t.like_count)}
        </button>
        <span style={{ flex: 1 }} />
        <span style={{ fontSize: 10, fontWeight: 600, letterSpacing: 0.8, color: meta }}>{t.author.name}</span>
        <button
          onClick={(e) => { e.stopPropagation(); onSave(t.id); }}
          aria-label="Save"
          className="reset"
          style={{ display: "flex", color: t.saved ? accent : meta, transition: "color .25s" }}
        >
          <BookmarkIcon size={13} fill={t.saved ? accent : "none"} />
        </button>
      </div>
    </article>
  );
}

export { fmt };
