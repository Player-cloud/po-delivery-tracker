"use client";

import { useEffect } from "react";
import * as Sentry from "@sentry/browser";

// Error tracking. No-op unless NEXT_PUBLIC_SENTRY_DSN is set at build time.
let started = false;

export default function SentryInit() {
  useEffect(() => {
    const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;
    if (!dsn || started) return;
    started = true;
    Sentry.init({
      dsn,
      environment: process.env.NEXT_PUBLIC_ENV ?? "production",
      tracesSampleRate: 0.1,
      sendDefaultPii: false,
    });
  }, []);
  return null;
}
