"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import StatusBadge from "@/components/StatusBadge";
import UrgencyBar from "@/components/UrgencyBar";
import GettingStarted from "@/components/GettingStarted";
import TourOverlay from "@/components/TourOverlay";
import { assigneeLabel } from "@/lib/status";
import { daysRemainingLabel } from "@/lib/urgency";
import { useCountUp } from "@/hooks/useCountUp";
import { card, h1, page } from "@/lib/ui";
import type { POLine } from "@/lib/types";

type Summary = {
  total_open: number;
  due_today: number;
  due_this_week: number;
  due_soon: number;
  later: number;
  overdue: number;
  completed: number;
  high_priority: number;
  total_pos: number;
  total_po_lines: number;
  pos_delivered: number;
  pos_closed: number;
  due_1_30: number;
};

// Single-stat cards — every one opens the PO Lines list, filtered.
const STATS: { key: keyof Summary; label: string; href: string; tone?: "danger" }[] = [
  { key: "due_1_30", label: "Due in 1–30 days", href: "/po-lines?due_within=30" },
  { key: "overdue", label: "Overdue", href: "/po-lines?status=Overdue", tone: "danger" },
  { key: "pos_delivered", label: "Delivered POs", href: "/po-lines?po_status=delivered" },
  { key: "completed", label: "Delivered lines", href: "/po-lines?delivery_status=complete" },
  { key: "high_priority", label: "High priority", href: "/po-lines?priority=high" },
];

function greeting() {
  const h = new Date().getHours();
  return h < 12 ? "Good morning" : h < 18 ? "Good afternoon" : "Good evening";
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [attention, setAttention] = useState<POLine[] | null>(null);
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [tourOpen, setTourOpen] = useState(false);

  useEffect(() => {
    let ignore = false;
    (async () => {
      try {
        const [s, a, me] = await Promise.all([
          apiFetch("/dashboard/summary").then((r) => (r.ok ? r.json() : Promise.reject())),
          apiFetch("/dashboard/attention").then((r) => (r.ok ? r.json() : Promise.reject())),
          apiFetch("/auth/me").then((r) => (r.ok ? r.json() : null)),
        ]);
        if (ignore) return;
        setSummary(s);
        setAttention(a);
        if (me) setName(me.full_name?.split(" ")[0] ?? me.email?.split("@")[0] ?? "");
      } catch {
        if (!ignore) setError("Could not load the dashboard");
      }
    })();
    return () => {
      ignore = true;
    };
  }, []);

  if (error) return <p className={`${page} text-overdue-on`}>{error}</p>;
  if (!summary || !attention) return <p className={`${page} text-muted`}>Loading…</p>;

  return (
    <div className={`${page} flex flex-col gap-5`}>
      <div className="animate-rise flex flex-col gap-0.5">
        <h1 className={h1}>
          {greeting()}
          {name && `, ${name}`}
        </h1>
        <span className="text-[12.5px] text-muted">
          {new Date().toLocaleDateString(undefined, {
            weekday: "long",
            day: "numeric",
            month: "long",
          })}
        </span>
      </div>

      <GettingStarted onStartTour={() => setTourOpen(true)} />

      {/* Totals — both open the full PO Lines list. */}
      <div className={`animate-rise ${card} grid grid-cols-2 divide-x divide-line overflow-hidden`}>
        <StatLink href="/po-lines" label="Purchase orders" value={summary.total_pos} />
        <StatLink href="/po-lines" label="PO lines" value={summary.total_po_lines} />
      </div>

      <div className="grid grid-cols-2 gap-3.5 sm:grid-cols-3 lg:grid-cols-5">
        {STATS.map((s, i) => (
          <StatCard
            key={s.key}
            label={s.label}
            value={summary[s.key]}
            href={s.href}
            tone={s.tone}
            delay={i * 60}
          />
        ))}
      </div>

      <UrgencyBar counts={summary} />

      <div className={`${card} animate-rise overflow-hidden`}>
        <div className="flex items-center justify-between border-b border-line px-5 py-3.5">
          <span className="font-display text-[13.5px] font-semibold">Needs attention</span>
          <Link href="/po-lines" className="text-xs text-accent hover:underline">
            View all &rarr;
          </Link>
        </div>

        {attention.length === 0 ? (
          <p className="px-5 py-8 text-sm text-faint">Nothing needs attention right now.</p>
        ) : (
          <>
            {/* Phones / small tablets: stacked rows */}
            <ul className="divide-y divide-line/70 md:hidden">
              {attention.map((l) => (
                <li key={l.id} className="flex flex-col gap-1.5 px-4 py-3">
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-semibold">
                      {l.po_number} <span className="text-faint">&middot; {l.po_line}</span>
                    </span>
                    <StatusBadge delivered={l.delivered} days_remaining={l.days_remaining} />
                  </div>
                  <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-[12px] text-muted">
                    <span className="font-mono">{l.promised_delivery}</span>
                    <span>· {daysRemainingLabel(l.days_remaining)}</span>
                    <span className="w-full truncate">{assigneeLabel(l.assigned_to)}</span>
                  </div>
                  <Link
                    href={`/po-lines/edit?id=${l.id}`}
                    className="text-[12px] text-accent hover:underline"
                  >
                    Edit
                  </Link>
                </li>
              ))}
            </ul>

            {/* Tablet landscape and up: table */}
            <div className="hidden overflow-x-auto md:block">
              <table className="w-full min-w-[560px] text-left text-[12.5px]">
                <thead>
                  <tr className="text-[10.5px] uppercase tracking-[0.04em] text-faint">
                    <th className="px-5 py-2.5 font-medium">PO / Line</th>
                    <th className="px-5 py-2.5 font-medium">Promised</th>
                    <th className="px-5 py-2.5 font-medium">Remaining</th>
                    <th className="px-5 py-2.5 font-medium">Assignee</th>
                    <th className="px-5 py-2.5 font-medium">Status</th>
                    <th className="px-5 py-2.5" />
                  </tr>
                </thead>
                <tbody>
                  {attention.map((l) => (
                    <tr key={l.id} className="border-t border-line/70 hover:bg-surface-tint">
                      <td className="px-5 py-3 font-semibold">
                        {l.po_number} <span className="text-faint">&middot; {l.po_line}</span>
                      </td>
                      <td className="px-5 py-3 font-mono text-muted">{l.promised_delivery}</td>
                      <td className="px-5 py-3 text-muted">{daysRemainingLabel(l.days_remaining)}</td>
                      <td className="px-5 py-3 text-muted">{assigneeLabel(l.assigned_to)}</td>
                      <td className="px-5 py-3">
                        <StatusBadge delivered={l.delivered} days_remaining={l.days_remaining} />
                      </td>
                      <td className="px-5 py-3">
                        <Link
                          href={`/po-lines/edit?id=${l.id}`}
                          className="text-accent hover:underline"
                        >
                          Edit
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>

      {tourOpen && <TourOverlay onClose={() => setTourOpen(false)} />}
    </div>
  );
}

function StatLink({ href, label, value }: { href: string; label: string; value: number }) {
  const shown = useCountUp(value);
  return (
    <Link
      href={href}
      className="flex flex-col gap-1 p-4 transition-colors hover:bg-surface-tint"
    >
      <span className="text-xs text-muted">{label}</span>
      <span className="font-display text-[28px] font-semibold tabular-nums">{shown}</span>
    </Link>
  );
}

function StatCard({
  label,
  value,
  href,
  tone,
  delay,
}: {
  label: string;
  value: number;
  href: string;
  tone?: "danger";
  delay: number;
}) {
  const shown = useCountUp(value);
  return (
    <Link
      href={href}
      className={`animate-rise ${card} flex flex-col gap-1 p-4 transition-colors hover:bg-surface-tint ${
        tone === "danger" ? "border-overdue/25 bg-overdue-tint hover:bg-overdue-tint/70" : ""
      }`}
      style={{ animationDelay: `${delay}ms` }}
    >
      <span className={`text-xs ${tone === "danger" ? "text-overdue-on" : "text-muted"}`}>
        {label}
      </span>
      <span
        className={`font-display text-[28px] font-semibold tabular-nums ${
          tone === "danger" ? "text-overdue-on" : ""
        }`}
      >
        {shown}
      </span>
    </Link>
  );
}
