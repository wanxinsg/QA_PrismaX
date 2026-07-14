import type { Block } from "@/lib/types";

/** Renders a published thread's body blocks (read-only). */
export function BlockRenderer({ blocks }: { blocks: Block[] }) {
  let firstParaSeen = false;
  return (
    <>
      {blocks.map((b, i) => {
        const html = b.html || b.text || "";
        switch (b.type) {
          case "h2":
            return (
              <h2 key={i} className="serif" style={{ margin: "42px 0 16px", fontWeight: 400, fontStyle: "italic", fontSize: 30, letterSpacing: -0.5, color: "var(--ink)" }} dangerouslySetInnerHTML={{ __html: html }} />
            );
          case "quote":
            return (
              <blockquote key={i} className="serif" style={{ margin: "0 0 22px", fontStyle: "italic", fontSize: 20, lineHeight: 1.6, color: "var(--ink)", paddingLeft: 18, borderLeft: "2px solid var(--accent)" }} dangerouslySetInnerHTML={{ __html: html }} />
            );
          case "bullet":
            return (
              <div key={i} style={{ display: "flex", gap: 10, alignItems: "baseline", margin: "0 0 8px" }}>
                <span style={{ color: "var(--accent)", fontSize: 18, lineHeight: 1.7 }}>•</span>
                <div className="serif" style={{ flex: 1, fontSize: 18, lineHeight: 1.7, color: "var(--ink2)" }} dangerouslySetInnerHTML={{ __html: html }} />
              </div>
            );
          case "code":
            return (
              <pre key={i} style={{ margin: "0 0 22px", fontFamily: "ui-monospace,Menlo,Consolas,monospace", fontSize: 14, lineHeight: 1.7, color: "var(--ink)", background: "var(--surface2)", border: "1px solid var(--line-soft)", borderRadius: 6, padding: "12px 14px", whiteSpace: "pre-wrap" }} dangerouslySetInnerHTML={{ __html: html }} />
            );
          case "divider":
            return <div key={i} style={{ padding: "14px 0" }}><div style={{ height: 1, background: "var(--line)" }} /></div>;
          case "image":
            return (
              <figure key={i} style={{ margin: "0 0 24px" }}>
                <div style={{ borderRadius: 6, overflow: "hidden", background: "#1a1c1a", boxShadow: "var(--shadow)" }}>
                  {b.src && <img src={b.src} alt={b.caption || ""} style={{ width: "100%", display: "block" }} />}
                </div>
                {b.caption && (
                  <figcaption style={{ textAlign: "center", fontSize: 11, color: "var(--meta)", marginTop: 12, fontStyle: "italic" }}>{b.caption}</figcaption>
                )}
              </figure>
            );
          default: {
            const isFirst = !firstParaSeen;
            firstParaSeen = true;
            return (
              <p
                key={i}
                className={isFirst ? "dropcap" : undefined}
                style={{ margin: "0 0 22px", fontSize: isFirst ? 17 : 15, lineHeight: isFirst ? 1.72 : 1.78, color: "var(--ink2)" }}
                dangerouslySetInnerHTML={{ __html: html }}
              />
            );
          }
        }
      })}
    </>
  );
}
