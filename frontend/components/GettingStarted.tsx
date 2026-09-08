"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { useLocalFlag } from "@/hooks/useLocalFlag";
import { card } from "@/lib/ui";

const DISMISS_KEY = "po-tracker:onboarding-dismissed";
const TOUR_KEY = "po-tracker:tour-done";

type Item = { label: string; href: string; done: boolean };

export default function GettingStarted({ onStartTour }: { onStartTour: () => void }) {
  const { isAdmin } = useAuth();
  const [dismissed, dismiss] = useLocalFlag(DISMISS_KEY);
  const [tourDone, markTourDone] = useLocalFlag(TOUR_KEY);
  const [teamAdded, setTeamAdded] = useState(false);
  const [hasLines, setHasLines] = useState(false);

  useEffect(() => {
    let ignore = false;
    (async () => {
      try {
        const [u, s] = await Promise.all([
          apiFetch("/users/assignable").then((r) => (r.ok ? r.json() : [])),
          apiFetch("/dashboard/summary").then((r) => (r.ok ? r.json() : null)),
        ]);
        if (ignore) return;
        setTeamAdded(Array.isArray(u) && u.length > 1);
        setHasLines(!!s && s.total_open + s.completed > 0);
      } catch {
        /* leave defaults */
      }
    })();
    return () => {
      ignore = true;
    };
  }, []);

  const items: Item[] = [
    ...(isAdmin ? [{ label: "Add your team", href: "/admin/users", done: teamAdded }] : []),
    { label: "Create your first PO line", href: "/po-lines/new", done: hasLines },
    ...(isAdmin
      ? [{ label: "Review the reminder thresholds", href: "/admin/thresholds", done: false }]
      : []),
  ];
  const doneCount = items.filter((i) => i.done).length + (tourDone ? 1 : 0);
  const totalCount = items.length + 1;

  if (dismissed || doneCount >= totalCount) return null;

  return (
    <div className={`${card} animate-rise w-full p-[17px] sm:max-w-md`}>
      <div className="mb-3 flex items-center justify-between">
        <span className="font-display text-[13.5px] font-semibold">Getting started</span>
        <span className="text-[11px] text-muted">
          {doneCount} / {totalCount}
        </span>
      </div>
      <ul className="flex flex-col gap-2.5 text-[12.5px]">
        {items.map((i) => (
          <li key={i.label}>
            <Link
              href={i.href}
              className={`flex items-center gap-2.5 ${i.done ? "text-muted line-through" : "hover:text-accent"}`}
            >
              <Check done={i.done} />
              {i.label}
            </Link>
          </li>
        ))}
        <li>
          <button
            onClick={() => {
              markTourDone();
              onStartTour();
            }}
            className={`flex items-center gap-2.5 ${tourDone ? "text-muted line-through" : "hover:text-accent"}`}
          >
            <Check done={tourDone} />
            Take the 2-minute tour
          </button>
        </li>
      </ul>
      <button
        onClick={dismiss}
        className="mt-3 text-[11px] text-faint hover:text-muted"
      >
        Dismiss
      </button>
    </div>
  );
}

function Check({ done }: { done: boolean }) {
  return done ? (
    <span className="flex h-4 w-4 items-center justify-center rounded-[5px] bg-ontrack">
      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3.5" strokeLinecap="round" aria-hidden>
        <path d="M4 12l5 5L20 6" />
      </svg>
    </span>
  ) : (
    <span className="h-4 w-4 shrink-0 rounded-[5px] border-[1.5px] border-line" aria-hidden />
  );
}
