"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearToken } from "@/lib/auth";
import { useAuth } from "@/lib/useAuth";

const LINKS = [
  { href: "/dashboard", label: "Dashboard", adminOnly: false },
  { href: "/po-lines", label: "PO Lines", adminOnly: false },
  { href: "/admin/thresholds", label: "Alert Thresholds", adminOnly: true },
  { href: "/admin/users", label: "Users", adminOnly: true },
  { href: "/admin/deletion-requests", label: "Deletion Requests", adminOnly: true },
];

export default function NavBar() {
  const { loggedIn, isAdmin } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  if (!loggedIn) return null;

  return (
    <nav
      aria-label="Primary"
      className="flex h-14 shrink-0 items-center gap-4 border-b border-line bg-surface px-4 sm:gap-6 sm:px-6"
    >
      <Link href="/dashboard" className="flex items-center gap-2.5">
        <span className="h-[22px] w-[22px] rounded-[7px] bg-accent" aria-hidden />
        <span className="font-display text-[15px] font-semibold">PO Tracker</span>
      </Link>

      <div className="flex items-center gap-0.5 overflow-x-auto text-[13.5px]">
        {LINKS.filter((l) => !l.adminOnly || isAdmin).map((l) => {
          const active = pathname === l.href || pathname.startsWith(l.href + "/");
          return (
            <Link
              key={l.href}
              href={l.href}
              aria-current={active ? "page" : undefined}
              className={`whitespace-nowrap rounded-lg px-3 py-1.5 transition-colors ${
                active
                  ? "bg-accent-soft font-semibold text-accent-hover"
                  : "text-muted hover:text-ink"
              }`}
            >
              {l.label}
            </Link>
          );
        })}
      </div>

      <div className="ml-auto flex items-center gap-3">
        <Link
          href="/po-lines/new"
          className="inline-flex items-center gap-1.5 rounded-full bg-accent px-3.5 py-2 text-[13px] font-semibold text-accent-on transition-colors hover:bg-accent-hover"
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" aria-hidden>
            <path d="M12 5v14M5 12h14" />
          </svg>
          <span className="hidden sm:inline">New PO Line</span>
        </Link>
        <button
          onClick={() => {
            clearToken();
            router.push("/login");
          }}
          className="text-[13px] text-muted hover:text-ink"
        >
          Log out
        </button>
      </div>
    </nav>
  );
}
