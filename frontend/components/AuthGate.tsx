"use client";

import { useEffect, useSyncExternalStore } from "react";
import { usePathname, useRouter } from "next/navigation";
import { getToken, subscribe } from "@/lib/auth";

// Routes a logged-out visitor is allowed to see. Everything else bounces to
// /login — the app is a static export, so this is the only auth gate there is.
const PUBLIC = new Set(["/login"]);

// `false` during SSR / the first hydration render, `true` once we're on the
// client. Guards against acting on the (always-null) server auth snapshot.
const subscribeNoop = () => () => {};

export default function AuthGate({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const hydrated = useSyncExternalStore(
    subscribeNoop,
    () => true,
    () => false,
  );
  const token = useSyncExternalStore(subscribe, getToken, () => null);

  const isPublic = PUBLIC.has(pathname);
  const blocked = hydrated && token === null && !isPublic;

  useEffect(() => {
    if (blocked) router.replace("/login");
  }, [blocked, router]);

  // Don't render protected content until the client confirms a token, and don't
  // render anything mid-redirect.
  if (!isPublic && (!hydrated || token === null)) return null;
  return <>{children}</>;
}
