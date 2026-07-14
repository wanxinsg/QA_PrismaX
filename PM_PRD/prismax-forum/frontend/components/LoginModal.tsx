"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { PresetUser } from "@/lib/types";
import { CloseIcon } from "./Icons";

export function LoginModal({ onClose, onSuccess }: { onClose: () => void; onSuccess: () => void }) {
  const [presets, setPresets] = useState<PresetUser[]>([]);
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.demoUsers().then(setPresets).catch(() => setPresets([]));
  }, []);

  async function login(payload: { external_id?: string; name?: string }) {
    if (busy) return;
    setBusy(true);
    try {
      await api.demoLogin(payload);
      onSuccess();
    } catch {
      setBusy(false);
    }
  }

  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 200,
        background: "rgba(26,28,26,0.45)",
        backdropFilter: "blur(4px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 20,
        animation: "fadeIn .25s ease",
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: "100%",
          maxWidth: 420,
          background: "var(--surface)",
          border: "1px solid var(--line-soft)",
          borderRadius: 14,
          padding: 28,
          boxShadow: "0 24px 60px rgba(26,28,26,0.22)",
          animation: "sheetIn .25s ease",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <div
              style={{
                fontSize: 10,
                fontWeight: 700,
                letterSpacing: 2,
                textTransform: "uppercase",
                color: "var(--accent)",
              }}
            >
              Demo Sign In
            </div>
            <h2 className="serif" style={{ margin: "8px 0 0", fontWeight: 300, fontStyle: "italic", fontSize: 30, color: "var(--ink)" }}>
              Join the discourse
            </h2>
          </div>
          <button onClick={onClose} className="reset icon-btn" style={{ width: 34, height: 34, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--meta)" }} aria-label="Close">
            <CloseIcon size={16} />
          </button>
        </div>

        <p style={{ fontSize: 12.5, lineHeight: 1.6, color: "var(--meta)", margin: "14px 0 18px" }}>
          This is a stub login for the demo. In production, PrismaX&rsquo;s own user system
          replaces this screen — no forum code changes.
        </p>

        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {presets.map((p) => (
            <button
              key={p.external_id}
              onClick={() => login({ external_id: p.external_id })}
              disabled={busy}
              className="reset menu-item"
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
                padding: "10px 12px",
                borderRadius: 10,
                border: "1px solid var(--line-soft)",
                textAlign: "left",
              }}
            >
              <span
                className="serif"
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: "50%",
                  background: p.avatar_color || "var(--accent)",
                  color: "#fff",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 14,
                  flexShrink: 0,
                }}
              >
                {p.name.charAt(0)}
              </span>
              <span style={{ fontSize: 14, fontWeight: 600, color: "var(--ink)" }}>{p.name}</span>
            </button>
          ))}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 10, margin: "18px 0" }}>
          <span style={{ flex: 1, height: 1, background: "var(--line-soft)" }} />
          <span style={{ fontSize: 10, letterSpacing: 1.2, textTransform: "uppercase", color: "var(--meta)" }}>or</span>
          <span style={{ flex: 1, height: 1, background: "var(--line-soft)" }} />
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (name.trim()) login({ name: name.trim() });
          }}
          style={{ display: "flex", gap: 8 }}
        >
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Enter any name…"
            style={{
              flex: 1,
              border: "1px solid var(--line-soft)",
              borderRadius: 10,
              padding: "11px 13px",
              outline: "none",
              fontSize: 14,
              color: "var(--ink)",
              background: "var(--surface)",
            }}
          />
          <button
            type="submit"
            disabled={busy || !name.trim()}
            className="reset btn-dark"
            style={{
              background: name.trim() ? "var(--ink)" : "var(--line)",
              color: "#FAF9F6",
              fontSize: 11,
              fontWeight: 700,
              letterSpacing: 1,
              textTransform: "uppercase",
              padding: "0 18px",
              borderRadius: 10,
              cursor: name.trim() ? "pointer" : "not-allowed",
            }}
          >
            Enter
          </button>
        </form>
      </div>
    </div>
  );
}
