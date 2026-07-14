export function Footer() {
  return (
    <footer style={{ background: "#F4F3F1", borderTop: "1px solid var(--line-soft)", marginTop: "auto" }}>
      <div
        style={{
          width: "100%",
          maxWidth: 1240,
          margin: "0 auto",
          padding: "30px clamp(16px,4vw,28px)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 20,
          flexWrap: "wrap",
        }}
      >
        <div>
          <div className="serif" style={{ fontWeight: 500, fontSize: 18, color: "var(--ink)" }}>
            Prisma<span style={{ fontStyle: "italic", fontWeight: 400 }}>(x)</span>
          </div>
          <div
            style={{
              fontSize: 10,
              letterSpacing: 1.4,
              textTransform: "uppercase",
              color: "var(--meta)",
              marginTop: 4,
            }}
          >
            The Digital Monograph · © 2026
          </div>
        </div>
        <div style={{ display: "flex", gap: 26 }}>
          {["Privacy", "Terms", "Contact"].map((l) => (
            <a
              key={l}
              href="#"
              className="nav-link"
              style={{
                fontSize: 11,
                fontWeight: 600,
                letterSpacing: 1,
                textTransform: "uppercase",
                color: "var(--meta)",
              }}
            >
              {l}
            </a>
          ))}
        </div>
      </div>
    </footer>
  );
}
