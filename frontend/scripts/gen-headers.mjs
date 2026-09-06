// Writes out/_headers for Cloudflare Pages after `next build`. CSP's connect-src
// is built from the API + Sentry origins so it's as tight as the deploy allows.
import { existsSync, writeFileSync } from "node:fs";

// `next build` auto-loads .env.production / .env.local; this standalone script
// does not, so load them here too. loadEnvFile never overwrites an already-set
// var, so precedence is load-order: shell env, then .env.local, then
// .env.production — matching Next's own precedence.
for (const f of [".env.local", ".env.production"]) {
  if (existsSync(f)) process.loadEnvFile(f);
}

const api = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000").replace(/\/+$/, "");
const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;
const sentryOrigin = dsn ? safeOrigin(dsn) : "";

const connectSrc = ["'self'", api, sentryOrigin, "https://*.sentry.io"]
  .filter(Boolean)
  .join(" ");

const csp = [
  "default-src 'self'",
  "script-src 'self' 'unsafe-inline'",
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: blob:",
  "font-src 'self' data:",
  `connect-src ${connectSrc}`,
  "frame-ancestors 'none'",
  "base-uri 'self'",
  "form-action 'self'",
].join("; ");

const body = `/*
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: geolocation=(), camera=(), microphone=()
  Strict-Transport-Security: max-age=31536000; includeSubDomains
  Content-Security-Policy: ${csp}
`;

writeFileSync("out/_headers", body);
console.log("wrote out/_headers");

function safeOrigin(u) {
  try {
    return new URL(u).origin;
  } catch {
    return "";
  }
}
