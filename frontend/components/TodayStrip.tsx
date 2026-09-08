"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";

type Summary = { overdue: number; due_today: number; due_this_week: number };

function Count({ dot, children }: { dot: string; children: React.ReactNode }) {
  return (
    <span className="flex shrink-0 items-center gap-1.5">
      <span className={`h-[7px] w-[7px] shrink-0 rounded-full ${dot}`} aria-hidden />
      {children}
    </span>
  );
}

export default function TodayStrip() {
  const { loggedIn } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const [s, setS] = useState<Summary | null>(null);

  useEffect(() => {
    if (!loggedIn) return;
    let ignore = false;
    (async () => {
      try {
        const res = await apiFetch("/dashboard/summary");
        if (res.ok && !ignore) setS(await res.json());
      } catch {
        /* strip just stays quiet */
      }
    })();
    return () => {
      ignore = true;
    };
  }, [loggedIn, pathname]);

  // "/" jumps to the PO Lines search from anywhere.
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const el = e.target as HTMLElement | null;
      if (e.key !== "/" || el?.matches("input, textarea, select")) return;
      e.preventDefault();
      router.push("/po-lines?focus=1");
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [router]);

  if (!loggedIn) return null;

  return (
    <div className="shrink-0 bg-strip">
      <div className="mx-auto flex h-10 max-w-6xl items-center gap-3 overflow-x-auto px-4 font-mono text-[12px] text-strip-ink sm:gap-5 sm:px-6 sm:text-[12.5px]">
        <span className="shrink-0 font-display text-[11px] tracking-[0.08em] text-strip-faint">
          TODAY
        </span>
        {s ? (
          <>
            <Count dot="bg-overdue">
              {s.overdue}&nbsp;overdue
            </Count>
            <Count dot="bg-today">
              {s.due_today}&nbsp;due&nbsp;today
            </Count>
            <Count dot="bg-ontrack">
              {s.due_this_week}&nbsp;this&nbsp;week
            </Count>
          </>
        ) : (
          <span className="text-strip-faint">loading…</span>
        )}
        <span className="hidden shrink-0 whitespace-nowrap text-strip-faint md:inline">
          reminders daily 10:00 UK
        </span>
        <span className="ml-auto hidden shrink-0 items-center gap-1.5 whitespace-nowrap text-strip-faint lg:flex">
          <kbd className="rounded border border-strip-faint/50 px-1.5 py-0.5 text-[11px]">/</kbd>
          search
        </span>
      </div>
    </div>
  );
}
