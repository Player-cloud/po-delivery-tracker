import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // The app is entirely client-rendered (data comes from the backend API), so it
  // ships as a static export to Cloudflare Pages — no Node server, no cold
  // starts. `npm run build` writes ./out. See docs/DEPLOYMENT.md §3.
  output: "export",
  images: { unoptimized: true },
};

export default nextConfig;
