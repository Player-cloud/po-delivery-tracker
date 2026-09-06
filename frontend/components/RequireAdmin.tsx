"use client";

import Link from "next/link";
import { useAuth } from "@/lib/useAuth";

/** Gates a page to Administrators. Renders children only when the current token
 *  carries the administrator role; otherwise a short message. */
export default function RequireAdmin({ children }: { children: React.ReactNode }) {
  const { loggedIn, isAdmin } = useAuth();

  if (!loggedIn) {
    return (
      <p className="p-8 text-muted">
        Please{" "}
        <Link href="/login" className="text-accent hover:underline">
          log in
        </Link>
        .
      </p>
    );
  }
  if (!isAdmin) {
    return <p className="p-8 text-overdue-on">Administrators only.</p>;
  }
  return <>{children}</>;
}
