"use client";

import { useRouter, usePathname, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useAuth } from "@/app/providers";
import { SearchIcon, MenuIcon } from "./Icons";

export function Header() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { user, logout, openLogin, requireAuth } = useAuth();

  const [searchOpen, setSearchOpen] = useState(false);
  const [query, setQuery] = useState(searchParams.get("q") || "");
  const [menuOpen, setMenuOpen] = useState(false);
  const [userMenu, setUserMenu] = useState(false);
  const userRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (userRef.current && !userRef.current.contains(e.target as Node)) setUserMenu(false);
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  function runSearch(value: string) {
    setQuery(value);
    const params = new URLSearchParams(Array.from(searchParams.entries()));
    if (value) params.set("q", value);
    else params.delete("q");
    router.replace(`/?${params.toString()}`, { scroll: false });
  }

  function compose() {
    if (requireAuth()) router.push("/compose");
    setMenuOpen(false);
  }

  const onDiscussion = pathname === "/";

  return (
    <header
      style={{
        position: "sticky",
        top: 0,
        zIndex: 50,
        backdropFilter: "saturate(140%) blur(12px)",
        background: "rgba(250,249,246,0.82)",
        borderBottom: "1px solid var(--line-soft)",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: 1240,
          margin: "0 auto",
          padding: "0 clamp(16px,4vw,28px)",
          height: 68,
          display: "flex",
          alignItems: "center",
          gap: 20,
        }}
      >
        <Link href="/" className="serif" style={{ display: "flex", alignItems: "baseline", gap: 1, color: "var(--ink)" }}>
          <span style={{ fontWeight: 500, fontSize: 25, letterSpacing: -1, lineHeight: 1 }}>Prisma</span>
          <span style={{ fontWeight: 400, fontStyle: "italic", fontSize: 14 }}>(x)</span>
        </Link>

        <nav className="desktop-only" style={{ display: "flex", alignItems: "center", gap: 26, marginLeft: 26, flex: 1, minWidth: 0 }}>
          <Link
            href="/"
            className="nav-link"
            style={{ position: "relative", fontSize: 12, fontWeight: onDiscussion ? 600 : 500, letterSpacing: 0.4, color: onDiscussion ? "var(--ink)" : "var(--meta)", padding: "6px 0" }}
          >
            Discussion
            {onDiscussion && <span style={{ position: "absolute", left: 0, bottom: -2, height: 1.5, width: "100%", background: "var(--accent)" }} />}
          </Link>
        </nav>

        <span className="mobile-only" style={{ flex: 1 }} />

        <button
          onClick={() => setSearchOpen((v) => !v)}
          aria-label="Search"
          className="reset icon-btn"
          style={{ width: 38, height: 38, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--ink2)" }}
        >
          <SearchIcon size={17} />
        </button>

        <button onClick={compose} className="reset btn-dark desktop-only" style={{ background: "var(--ink)", color: "#FAF9F6", fontSize: 11, fontWeight: 700, letterSpacing: 1.2, textTransform: "uppercase", padding: "11px 20px", borderRadius: 30, whiteSpace: "nowrap" }}>
          New Post
        </button>

        {user ? (
          <div ref={userRef} className="desktop-only" style={{ position: "relative" }}>
            <button onClick={() => setUserMenu((v) => !v)} className="reset serif" aria-label="Account" style={{ width: 38, height: 38, borderRadius: "50%", background: user.avatar_color || "var(--accent)", color: "#fff", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14 }}>
              {user.initials}
            </button>
            {userMenu && (
              <div style={{ position: "absolute", right: 0, top: "100%", marginTop: 8, width: 190, background: "var(--surface)", border: "1px solid var(--line-soft)", borderRadius: 10, boxShadow: "0 16px 40px rgba(26,28,26,0.16)", padding: 6, animation: "sheetIn .18s ease" }}>
                <div style={{ padding: "8px 10px 6px", fontSize: 13, fontWeight: 700, color: "var(--ink)" }}>{user.name}</div>
                <UserMenuItem onClick={() => { setUserMenu(false); router.push("/drafts"); }}>My Drafts</UserMenuItem>
                <UserMenuItem onClick={() => { setUserMenu(false); router.push("/saved"); }}>Saved</UserMenuItem>
                <UserMenuItem onClick={() => { setUserMenu(false); logout(); }}>Sign Out</UserMenuItem>
              </div>
            )}
          </div>
        ) : (
          <button onClick={openLogin} className="reset desktop-only hover-accent" style={{ fontSize: 11, fontWeight: 700, letterSpacing: 0.8, textTransform: "uppercase", color: "var(--meta)" }}>
            Sign In
          </button>
        )}

        <button onClick={() => setMenuOpen((v) => !v)} aria-label="Menu" className="reset mobile-only" style={{ width: 40, height: 40, display: "flex", alignItems: "center", justifyContent: "center", color: "var(--ink)" }}>
          <MenuIcon open={menuOpen} />
        </button>
      </div>

      {searchOpen && (
        <div style={{ borderTop: "1px solid var(--line-soft)", background: "rgba(250,249,246,0.92)", animation: "fadeIn .3s ease" }}>
          <div style={{ width: "100%", maxWidth: 1240, margin: "0 auto", padding: "14px clamp(16px,4vw,28px)", display: "flex", alignItems: "center", gap: 12 }}>
            <SearchIcon size={18} />
            <input
              autoFocus
              value={query}
              onChange={(e) => runSearch(e.target.value)}
              placeholder="Search threads, authors, topics…"
              className="serif"
              style={{ flex: 1, border: "none", outline: "none", background: "none", fontSize: 22, fontStyle: "italic", color: "var(--ink)" }}
            />
            <button onClick={() => setSearchOpen(false)} className="reset hover-accent" style={{ fontSize: 11, fontWeight: 600, letterSpacing: 1, textTransform: "uppercase", color: "var(--meta)" }}>Close</button>
          </div>
        </div>
      )}

      {menuOpen && (
        <div className="mobile-only" style={{ borderTop: "1px solid var(--line-soft)", background: "rgba(250,249,246,0.97)", animation: "sheetIn .25s ease" }}>
          <div style={{ width: "100%", maxWidth: 1240, margin: "0 auto", padding: "14px clamp(16px,4vw,28px) 20px", display: "flex", flexDirection: "column", gap: 2 }}>
            <Link href="/" onClick={() => setMenuOpen(false)} className="serif" style={{ fontStyle: "italic", fontSize: 22, color: "var(--ink)", padding: "12px 0" }}>Discussion</Link>
            {user ? (
              <button onClick={() => { setMenuOpen(false); logout(); }} className="reset" style={{ textAlign: "left", fontSize: 13, fontWeight: 600, color: "var(--meta)", padding: "12px 0" }}>Sign Out ({user.name})</button>
            ) : (
              <button onClick={() => { setMenuOpen(false); openLogin(); }} className="reset" style={{ textAlign: "left", fontSize: 13, fontWeight: 600, color: "var(--meta)", padding: "12px 0" }}>Sign In</button>
            )}
            <button onClick={compose} className="reset btn-dark" style={{ background: "var(--ink)", color: "#FAF9F6", fontSize: 12, fontWeight: 700, letterSpacing: 1.2, textTransform: "uppercase", padding: 15, borderRadius: 30, marginTop: 12 }}>Write New Post</button>
          </div>
        </div>
      )}
    </header>
  );
}

function UserMenuItem({ children, onClick }: { children: React.ReactNode; onClick: () => void }) {
  return (
    <button onClick={onClick} className="reset menu-item" style={{ width: "100%", textAlign: "left", padding: "8px 10px", borderRadius: 6, fontSize: 13, fontWeight: 500, color: "var(--ink)" }}>
      {children}
    </button>
  );
}
