"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import type { Block, BlockType } from "@/lib/types";
import { ArrowLeftIcon, CloseIcon, ImageIcon, PlusIcon } from "@/components/Icons";
import { useAuth, useToast } from "@/app/providers";

interface EditorBlock extends Block {
  id: string;
}

const CATEGORIES = ["Discourse", "Case Study", "Editorial", "Protocol"];

const BLOCK_TYPES: { type: BlockType; label: string; glyph: string }[] = [
  { type: "p", label: "Text", glyph: "T" },
  { type: "h2", label: "Heading", glyph: "H" },
  { type: "quote", label: "Quote", glyph: "❝" },
  { type: "bullet", label: "Bullet list", glyph: "•" },
  { type: "code", label: "Code", glyph: "‹›" },
  { type: "divider", label: "Divider", glyph: "—" },
  { type: "image", label: "Image", glyph: "▣" },
];

const STYLE: Record<string, React.CSSProperties> = {
  p: { minHeight: 30, outline: "none", fontFamily: "var(--font-newsreader)", fontSize: 18, lineHeight: 1.8, color: "var(--ink2)" },
  h2: { minHeight: 38, outline: "none", fontFamily: "var(--font-newsreader)", fontStyle: "italic", fontWeight: 400, fontSize: 30, lineHeight: 1.3, letterSpacing: -0.5, color: "var(--ink)" },
  quote: { minHeight: 30, outline: "none", fontFamily: "var(--font-newsreader)", fontStyle: "italic", fontSize: 20, lineHeight: 1.6, color: "var(--ink)", paddingLeft: 18, borderLeft: "2px solid var(--accent)" },
  bullet: { minHeight: 28, outline: "none", fontFamily: "var(--font-newsreader)", fontSize: 18, lineHeight: 1.7, color: "var(--ink2)" },
  code: { minHeight: 30, outline: "none", fontFamily: "ui-monospace,Menlo,Consolas,monospace", fontSize: 14, lineHeight: 1.7, color: "var(--ink)", background: "var(--surface2)", border: "1px solid var(--line-soft)", borderRadius: 6, padding: "12px 14px", whiteSpace: "pre-wrap" },
};
const PH: Record<string, string> = { p: "Write something, or click + to add a block", h2: "Heading", quote: "Quote", bullet: "List item", code: "Code snippet" };

let bidCounter = 100;
const nid = () => `b${++bidCounter}`;

function Editor() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const editId = searchParams.get("id");
  const { user, loading: authLoading, requireAuth } = useAuth();
  const toast = useToast();

  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("Discourse");
  const [cover, setCover] = useState<string | null>(null);
  const [blocks, setBlocks] = useState<EditorBlock[]>([{ id: "b1", type: "p", html: "", text: "" }]);
  const [menuOpenId, setMenuOpenId] = useState<string | null>(null);
  const [dragId, setDragId] = useState<string | null>(null);
  const [overId, setOverId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const nodes = useRef<Record<string, HTMLDivElement | null>>({});
  const focusId = useRef<string | null>(null);
  const coverInput = useRef<HTMLInputElement>(null);
  const imageInput = useRef<HTMLInputElement>(null);
  const pendingAfter = useRef<string | null>(null);

  // Auth gate.
  useEffect(() => {
    if (!authLoading && !user) requireAuth();
  }, [authLoading, user, requireAuth]);

  // Load an existing draft for editing.
  useEffect(() => {
    if (!editId) return;
    api.getThread(Number(editId)).then((t) => {
      setTitle(t.title);
      setCategory(t.category);
      setCover(t.cover_image || null);
      const loaded = (t.content || []).map((b) => ({ ...b, id: nid() }));
      setBlocks(loaded.length ? loaded : [{ id: "b1", type: "p", html: "", text: "" }]);
    }).catch(() => toast("Could not load draft."));
  }, [editId]);

  // Focus the block queued after an add.
  useEffect(() => {
    if (focusId.current) {
      const n = nodes.current[focusId.current];
      if (n) {
        n.focus();
        caretEnd(n);
      }
      focusId.current = null;
    }
  });

  function setBlockText(id: string, html: string, text: string) {
    setBlocks((prev) => prev.map((b) => (b.id === id ? { ...b, html, text } : b)));
  }
  function setCaption(id: string, caption: string) {
    setBlocks((prev) => prev.map((b) => (b.id === id ? { ...b, caption } : b)));
  }

  function addBlock(afterId: string, type: BlockType) {
    const nb: EditorBlock = { id: nid(), type, html: "", text: "", caption: "" };
    setBlocks((prev) => {
      const i = prev.findIndex((b) => b.id === afterId);
      const arr = [...prev];
      arr.splice(i + 1, 0, nb);
      return arr;
    });
    setMenuOpenId(null);
    if (type !== "divider" && type !== "image") focusId.current = nb.id;
  }

  function removeBlock(id: string) {
    setBlocks((prev) => {
      if (prev.length <= 1) return prev;
      const i = prev.findIndex((b) => b.id === id);
      const neighbor = prev[i - 1] || prev[i + 1];
      if (neighbor) focusId.current = neighbor.id;
      return prev.filter((b) => b.id !== id);
    });
  }

  function onKeyDown(id: string, e: React.KeyboardEvent<HTMLDivElement>) {
    const b = blocks.find((x) => x.id === id);
    if (e.key === "Enter" && !e.shiftKey) {
      if (b?.type === "code") return;
      e.preventDefault();
      addBlock(id, "p");
    } else if (e.key === "Backspace") {
      const node = nodes.current[id];
      if (node && node.textContent === "" && blocks.length > 1) {
        e.preventDefault();
        removeBlock(id);
      }
    }
  }

  function pickImage(afterId: string) {
    pendingAfter.current = afterId;
    setMenuOpenId(null);
    setTimeout(() => imageInput.current?.click(), 0);
  }

  function onImageFile(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;
    const rd = new FileReader();
    rd.onload = () => {
      const nb: EditorBlock = { id: nid(), type: "image", src: rd.result as string, html: "", text: "", caption: "" };
      const after = pendingAfter.current;
      setBlocks((prev) => {
        const i = prev.findIndex((b) => b.id === after);
        const arr = [...prev];
        arr.splice((i < 0 ? arr.length - 1 : i) + 1, 0, nb);
        return arr;
      });
    };
    rd.readAsDataURL(f);
    e.target.value = "";
  }

  function onCoverFile(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;
    const rd = new FileReader();
    rd.onload = () => setCover(rd.result as string);
    rd.readAsDataURL(f);
    e.target.value = "";
  }

  function reorder(targetId: string) {
    setBlocks((prev) => {
      const from = prev.findIndex((b) => b.id === dragId);
      const to = prev.findIndex((b) => b.id === targetId);
      if (from < 0 || to < 0 || from === to) return prev;
      const arr = [...prev];
      const [m] = arr.splice(from, 1);
      arr.splice(to, 0, m);
      return arr;
    });
    setOverId(null);
  }

  const wordCount = blocks.reduce((n, b) => n + (b.text && b.text.trim() ? b.text.trim().split(/\s+/).length : 0), 0);
  const canPublish = title.trim().length > 0;

  function payload(status: "draft" | "published") {
    return {
      title: title.trim(),
      category,
      cover_image: cover,
      status,
      content: blocks.map(({ type, html, text, caption, src }) => ({ type, html, text, caption, src })),
    };
  }

  async function save(status: "draft" | "published") {
    if (!requireAuth()) return;
    if (status === "published" && !canPublish) return;
    if (busy) return;
    setBusy(true);
    try {
      if (editId) {
        await api.updateThread(Number(editId), payload(status));
      } else {
        await api.createThread(payload(status));
      }
      toast(status === "published" ? "Thread published to the community." : "Draft saved.");
      router.push(status === "published" ? "/" : "/drafts");
    } catch {
      toast("Could not save. Are you signed in?");
      setBusy(false);
    }
  }

  return (
    <div className="view-in">
      <div style={{ width: "100%", maxWidth: 760, margin: "0 auto", padding: "clamp(28px,5vw,52px) clamp(16px,5vw,28px) 60px" }}>
        <button onClick={() => router.push("/")} className="reset hover-accent" style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11, fontWeight: 700, letterSpacing: 1.2, textTransform: "uppercase", color: "var(--meta)", marginBottom: 30 }}>
          <ArrowLeftIcon size={15} /> Discard &amp; Return
        </button>

        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, marginBottom: 18 }}>
          <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: 1.8, textTransform: "uppercase", color: "var(--accent)" }}>{editId ? "Edit Monograph" : "New Monograph"} · Draft</span>
          <span style={{ display: "flex", alignItems: "center", gap: 7, fontSize: 10, fontWeight: 600, letterSpacing: 0.8, textTransform: "uppercase", color: "var(--meta)" }}>
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#8FB07A" }} />{wordCount} {wordCount === 1 ? "word" : "words"}
          </span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", marginBottom: 22 }}>
          <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: 1.2, textTransform: "uppercase", color: "var(--meta)", marginRight: 4 }}>Category</span>
          {CATEGORIES.map((c) => {
            const on = category === c;
            return (
              <button key={c} onClick={() => setCategory(c)} className="reset" style={{ fontSize: 11, fontWeight: 600, letterSpacing: 0.5, padding: "7px 14px", borderRadius: 20, transition: "all .25s", border: `1px solid ${on ? "var(--accent)" : "var(--line)"}`, background: on ? "var(--accent)" : "none", color: on ? "#FAF9F6" : "var(--ink2)" }}>{c}</button>
            );
          })}
        </div>

        {cover ? (
          <div className="fade-in" style={{ position: "relative", borderRadius: 8, overflow: "hidden", marginBottom: 24, boxShadow: "var(--shadow)" }}>
            <div style={{ width: "100%", height: 260, backgroundImage: `url('${cover}')`, backgroundSize: "cover", backgroundPosition: "center" }} />
            <button onClick={() => setCover(null)} className="reset" style={{ position: "absolute", top: 12, right: 12, background: "rgba(26,28,26,0.72)", color: "#FAF9F6", fontSize: 10, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", padding: "7px 12px", borderRadius: 20, backdropFilter: "blur(4px)" }}>Remove cover</button>
          </div>
        ) : (
          <button onClick={() => coverInput.current?.click()} className="reset hover-accent" style={{ width: "100%", background: "rgba(140,115,85,0.03)", border: "1px dashed var(--line)", borderRadius: 8, padding: 18, marginBottom: 24, display: "flex", alignItems: "center", justifyContent: "center", gap: 10, fontSize: 12, fontWeight: 600, letterSpacing: 0.4, color: "var(--meta)" }}>
            <ImageIcon size={17} /> Add a cover image
          </button>
        )}

        <input ref={coverInput} type="file" accept="image/*" onChange={onCoverFile} style={{ display: "none" }} />
        <input ref={imageInput} type="file" accept="image/*" onChange={onImageFile} style={{ display: "none" }} />

        <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Draft Title" className="serif" style={{ width: "100%", border: "none", outline: "none", background: "none", fontWeight: 300, fontStyle: "italic", fontSize: "clamp(38px,6vw,56px)", lineHeight: 1.05, letterSpacing: -1.5, color: "var(--ink)", marginBottom: 18, display: "block" }} />

        <div style={{ display: "flex", flexDirection: "column", gap: 1, minHeight: 280 }}>
          {blocks.map((b) => (
            <div
              key={b.id}
              draggable={dragId === b.id}
              onDragOver={(e) => { e.preventDefault(); if (overId !== b.id) setOverId(b.id); }}
              onDrop={(e) => { e.preventDefault(); reorder(b.id); }}
              onDragEnd={() => { setDragId(null); setOverId(null); }}
              style={{ position: "relative", display: "flex", gap: 4, alignItems: "flex-start", padding: "2px 0", borderRadius: 6 }}
            >
              {overId === b.id && dragId && dragId !== b.id && (
                <div style={{ position: "absolute", top: -1, left: 52, right: 0, height: 2, background: "var(--accent)", borderRadius: 2 }} />
              )}
              <div style={{ flexShrink: 0, width: 48, display: "flex", justifyContent: "flex-end", gap: 1, paddingTop: 6 }}>
                <button onClick={() => setMenuOpenId(menuOpenId === b.id ? null : b.id)} title="Add block" className="reset icon-btn" style={{ width: 22, height: 22, borderRadius: 5, display: "flex", alignItems: "center", justifyContent: "center", color: "var(--meta)" }}><PlusIcon size={15} /></button>
                <button onMouseDown={() => setDragId(b.id)} onMouseUp={() => setDragId(null)} title="Drag to reorder" className="reset icon-btn" style={{ width: 22, height: 22, borderRadius: 5, display: "flex", alignItems: "center", justifyContent: "center", color: "var(--meta)", cursor: "grab" }}>
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><circle cx="9" cy="6" r="1.7" /><circle cx="15" cy="6" r="1.7" /><circle cx="9" cy="12" r="1.7" /><circle cx="15" cy="12" r="1.7" /><circle cx="9" cy="18" r="1.7" /><circle cx="15" cy="18" r="1.7" /></svg>
                </button>
              </div>

              <div style={{ flex: 1, minWidth: 0, position: "relative" }}>
                {["p", "h2", "quote", "bullet", "code"].includes(b.type) && (
                  <div style={{ display: "flex", gap: 10, alignItems: "baseline" }}>
                    {b.type === "bullet" && <span style={{ color: "var(--accent)", fontSize: 18, lineHeight: 1.7, userSelect: "none" }}>•</span>}
                    <div
                      ref={(n) => {
                        nodes.current[b.id] = n;
                        if (n && n.innerHTML !== (b.html || "") && document.activeElement !== n) n.innerHTML = b.html || "";
                      }}
                      contentEditable
                      suppressContentEditableWarning
                      data-ph={PH[b.type] || "Write something…"}
                      onInput={(e) => setBlockText(b.id, e.currentTarget.innerHTML, e.currentTarget.textContent || "")}
                      onKeyDown={(e) => onKeyDown(b.id, e)}
                      style={{ flex: 1, minWidth: 0, ...STYLE[b.type] }}
                    />
                  </div>
                )}
                {b.type === "image" && (
                  <figure style={{ margin: "10px 0" }}>
                    <div style={{ position: "relative", borderRadius: 6, overflow: "hidden", boxShadow: "var(--shadow)" }}>
                      <div style={{ width: "100%", height: "clamp(180px,40vw,300px)", backgroundImage: b.src ? `url('${b.src}')` : "none", backgroundSize: "cover", backgroundPosition: "center", backgroundColor: "#E3E2E0" }} />
                      <button onClick={() => removeBlock(b.id)} title="Remove" className="reset" style={{ position: "absolute", top: 10, right: 10, background: "rgba(26,28,26,0.7)", color: "#FAF9F6", width: 28, height: 28, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", backdropFilter: "blur(4px)" }}><CloseIcon size={14} /></button>
                    </div>
                    <div
                      ref={(n) => { if (n && n.textContent !== (b.caption || "") && document.activeElement !== n) n.textContent = b.caption || ""; }}
                      contentEditable
                      suppressContentEditableWarning
                      data-ph="Add a caption…"
                      onInput={(e) => setCaption(b.id, e.currentTarget.textContent || "")}
                      style={{ textAlign: "center", outline: "none", fontSize: 11, color: "var(--meta)", fontStyle: "italic", marginTop: 10, minHeight: 16 }}
                    />
                  </figure>
                )}
                {b.type === "divider" && <div style={{ padding: "14px 0" }}><div style={{ height: 1, background: "var(--line)" }} /></div>}

                {menuOpenId === b.id && (
                  <div style={{ position: "absolute", left: 0, top: "100%", zIndex: 30, marginTop: 4, width: 212, background: "var(--surface)", border: "1px solid var(--line-soft)", borderRadius: 10, boxShadow: "0 16px 40px rgba(26,28,26,0.16)", padding: 6, animation: "sheetIn .18s ease" }}>
                    <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: 1.4, textTransform: "uppercase", color: "var(--meta)", padding: "6px 8px 5px" }}>Add block below</div>
                    {BLOCK_TYPES.map((bt) => (
                      <button key={bt.type} onClick={() => (bt.type === "image" ? pickImage(b.id) : addBlock(b.id, bt.type))} className="reset menu-item" style={{ width: "100%", textAlign: "left", display: "flex", alignItems: "center", gap: 11, padding: 8, borderRadius: 6, fontSize: 13, fontWeight: 500, color: "var(--ink)" }}>
                        <span className="serif" style={{ flexShrink: 0, width: 26, height: 26, borderRadius: 6, background: "var(--surface2)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, color: "var(--accent)" }}>{bt.glyph}</span>
                        {bt.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        <div style={{ position: "sticky", bottom: 0, marginTop: 30, padding: "16px 0", background: "linear-gradient(180deg,rgba(250,249,246,0) 0%,var(--bg) 40%)", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16, flexWrap: "wrap" }}>
          <span style={{ fontSize: 11, fontWeight: 600, letterSpacing: 0.6, color: "var(--meta)" }}>{wordCount} {wordCount === 1 ? "word" : "words"}</span>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <button onClick={() => save("draft")} disabled={busy} className="reset btn-outline" style={{ border: "1px solid var(--line)", borderRadius: 26, padding: "11px 20px", fontSize: 11, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", color: "var(--ink2)" }}>Save Draft</button>
            <button onClick={() => save("published")} disabled={busy || !canPublish} className="reset" style={{ background: canPublish ? "var(--ink)" : "var(--line)", color: "#FAF9F6", fontSize: 11, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", padding: "12px 24px", borderRadius: 26, cursor: canPublish ? "pointer" : "not-allowed", opacity: canPublish ? 1 : 0.55, transition: "all .25s" }}>Publish Thread</button>
          </div>
        </div>
      </div>
    </div>
  );
}

function caretEnd(node: HTMLElement) {
  try {
    const r = document.createRange();
    r.selectNodeContents(node);
    r.collapse(false);
    const s = window.getSelection();
    s?.removeAllRanges();
    s?.addRange(r);
  } catch {
    /* ignore */
  }
}

export default function ComposePage() {
  return (
    <Suspense fallback={null}>
      <Editor />
    </Suspense>
  );
}
