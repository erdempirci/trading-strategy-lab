import type { NextConfig } from "next";

// The browser talks only to this app; /api/* is proxied server-side to the
// FastAPI service, so no CORS setup or exposed API URL is needed.
const API_URL = (process.env.API_URL || "https://trading-strategy-lab-omega.vercel.app").replace(/\/$/, "");

const nextConfig: NextConfig = {
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API_URL}/:path*` }];
  },
};

export default nextConfig;
