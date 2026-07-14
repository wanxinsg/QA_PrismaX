import type { NextConfig } from "next";

// Backend origin the API proxy forwards to (server-side only, not exposed to the
// browser). Defaults to the local FastAPI service.
const BACKEND_ORIGIN = process.env.BACKEND_ORIGIN || "http://localhost:8085";

const nextConfig: NextConfig = {
  // Proxy /api/* to the FastAPI backend so the browser only ever talks to this
  // origin — no CORS, and the session cookie stays same-origin. Works behind any
  // host/proxy (IP, internal IP, or a future domain).
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${BACKEND_ORIGIN}/api/:path*` }];
  },
};

export default nextConfig;
