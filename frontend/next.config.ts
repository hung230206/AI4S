import type {NextConfig} from "next";
import path from "node:path";
const nextConfig: NextConfig = {
  output: process.env.BUILD_STANDALONE === "true" ? "standalone" : undefined,
  poweredByHeader: false,
  devIndicators: false,
  turbopack: {root: path.resolve(__dirname)},
  // OCR can run for 75s; keep the same-origin proxy alive long enough to return its result/error.
  experimental: {proxyTimeout: 120000},
  allowedDevOrigins: (process.env.LAN_ALLOWED_HOSTS || "").split(",").map(value => value.trim()).filter(Boolean),
  async rewrites() {
    const backend = process.env.API_PROXY_TARGET || "http://127.0.0.1:8000";
    return [{source: "/api/v1/:path*", destination: `${backend}/api/v1/:path*`}];
  },
  async headers() {
    return [{source: "/:path*", headers: [{key: "X-Content-Type-Options", value: "nosniff"}, {key: "Referrer-Policy", value: "same-origin"}, {key: "X-Frame-Options", value: "DENY"}, {key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=(), payment=(), usb=()"}]}];
  }
};
export default nextConfig;
