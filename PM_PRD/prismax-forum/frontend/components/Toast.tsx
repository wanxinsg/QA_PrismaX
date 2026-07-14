export function Toast({ message }: { message: string }) {
  return (
    <div
      style={{
        position: "fixed",
        left: "50%",
        bottom: 32,
        zIndex: 100,
        transform: "translateX(-50%)",
        background: "var(--ink)",
        color: "#FAF9F6",
        fontSize: 13,
        fontWeight: 600,
        padding: "13px 22px",
        borderRadius: 30,
        boxShadow: "0 16px 40px rgba(26,28,26,0.25)",
        animation: "toastIn .35s cubic-bezier(.2,.7,.2,1)",
        display: "flex",
        alignItems: "center",
        gap: 10,
      }}
    >
      <span style={{ width: 7, height: 7, borderRadius: "50%", background: "#9FD8A8" }} />
      {message}
    </div>
  );
}
