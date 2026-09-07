"use client";

import { useEffect, useState } from "react";
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
  const [open, setOpen] = useState(false);

  // Close the mobile menu on Escape.
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  if (!loggedIn) return null;

  const links = LINKS.filter((l) => !l.adminOnly || isAdmin);
  const isActive = (href: string) => pathname === href || pathname.startsWith(href + "/");

  function logOut() {
    setOpen(false);
    clearToken();
    router.push("/login");
  }

  return (
    <header className="relative z-40 shrink-0 border-b border-line bg-surface">
      <nav
        aria-label="Primary"
        className="mx-auto flex h-14 max-w-6xl items-center gap-4 px-4 sm:gap-6 sm:px-6"
      >
        <Link
          href="/dashboard"
          onClick={() => setOpen(false)}
          className="flex shrink-0 items-center gap-2.5"
        >
          <span className="h-[22px] w-[22px] rounded-[7px] bg-accent" aria-hidden />
          <span className="font-display text-[15px] font-semibold">PO Tracker</span>
        </Link>

        {/* Desktop: inline tabs */}
        <div className="hidden items-center gap-0.5 text-[13.5px] lg:flex">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              aria-current={isActive(l.href) ? "page" : undefined}
              className={`whitespace-nowrap rounded-lg px-3 py-1.5 transition-colors ${
                isActive(l.href)
                  ? "bg-accent-soft font-semibold text-accent-hover"
                  : "text-muted hover:text-ink"
              }`}
            >
              {l.label}
            </Link>
          ))}
        </div>

        {/* Desktop: actions */}
        <div className="ml-auto hidden items-center gap-3 lg:flex">
          <Link
            href="/po-lines/new"
            className="inline-flex items-center gap-1.5 rounded-full bg-accent px-3.5 py-2 text-[13px] font-semibold text-accent-on transition-colors hover:bg-accent-hover"
          >
            <PlusIcon />
            New PO Line
          </Link>
          <button onClick={logOut} className="text-[13px] text-muted hover:text-ink">
            Log out
          </button>
        </div>

        {/* Mobile / tablet: hamburger */}
        <button
          onClick={() => setOpen((v) => !v)}
          aria-label={open ? "Close menu" : "Open menu"}
          aria-expanded={open}
          aria-controls="mobile-menu"
          className="ml-auto flex h-9 w-9 items-center justify-center rounded-lg text-ink hover:bg-page lg:hidden"
        >
          {open ? <CloseIcon /> : <MenuIcon />}
        </button>
      </nav>

      {/* Mobile / tablet: dropdown panel */}
      {open && (
        <>
          <button
            aria-hidden
            tabIndex={-1}
            onClick={() => setOpen(false)}
            className="fixed inset-0 top-14 z-30 cursor-default bg-strip/20 lg:hidden"
          />
          <div
            id="mobile-menu"
            className="absolute inset-x-0 top-full z-40 flex flex-col gap-1 border-b border-line bg-surface p-3 shadow-card lg:hidden"
          >
            {links.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                onClick={() => setOpen(false)}
                aria-current={isActive(l.href) ? "page" : undefined}
                className={`rounded-lg px-3 py-2.5 text-sm transition-colors ${
                  isActive(l.href)
                    ? "bg-accent-soft font-semibold text-accent-hover"
                    : "text-ink hover:bg-page"
                }`}
              >
                {l.label}
              </Link>
            ))}
            <Link
              href="/po-lines/new"
              onClick={() => setOpen(false)}
              className="mt-1 inline-flex items-center justify-center gap-1.5 rounded-lg bg-accent px-3 py-2.5 text-sm font-semibold text-accent-on"
            >
              <PlusIcon />
              New PO Line
            </Link>
            <button
              onClick={logOut}
              className="rounded-lg px-3 py-2.5 text-left text-sm text-muted hover:bg-page"
            >
              Log out
            </button>
          </div>
        </>
      )}
    </header>
  );
}

function PlusIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" aria-hidden>
      <path d="M12 5v14M5 12h14" />
    </svg>
  );
}

function MenuIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden>
      <path d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden>
      <path d="M6 6l12 12M18 6L6 18" />
    </svg>
  );
}
