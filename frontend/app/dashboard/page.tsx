"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import StatusBadge from "@/components/StatusBadge";
import UrgencyBar from "@/components/UrgencyBar";
import GettingStarted from "@/components/GettingStarted";
import TourOverlay from "@/components/TourOverlay";
import { daysRemainingLabel } from "@/lib/urgency";
import { useCountUp } from "@/hooks/useCountUp";
import { card, h1, page } from "@/lib/ui";

type Summary = {
  total_open: number;
  due_today: number;
  due_this_week: number;
  due_soon: number;
  later: number;
  overdue: number;
  completed: number;
  high_priority: number;
};

type AttentionLine = {
  id: number;
  po_number: string;
  po_line: number;
  promised_delivery: string;
  days_remaining: number;
  delivered: boolean;
  assigned_to: { id: number; email: string } | null;
};

const KPIS: { key: keyof Summary; label: string; tone?: "danger" }[] = [
  { key: "due_today", label: "Due today" },
  { key: "overdue", label: "Overdue", tone: "danger" },
  { key: "total_open", label: "Total open" },
  { key: "high_priority", label: "High priority" },
];

function greeting() {
  const h = new Date().getHours();
  return h < 12 ? "Good morning" : h < 18 ? "Good afternoon" : "Good evening";
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [attention, setAttention] = useState<AttentionLine[] | null>(null);
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
        if (me?.email) setName(me.email.split("@")[0]);
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

      <div className="grid gap-4 md:grid-cols-[288px_1fr]">
        <GettingStarted onStartTour={() => setTourOpen(true)} />

        <div className="grid gap-3.5 sm:grid-cols-2">
          {KPIS.map((k, i) => (
            <KpiCard key={k.key} label={k.label} value={summary[k.key]} tone={k.tone} delay={i * 60} />
          ))}
          <div className="sm:col-span-2">
            <UrgencyBar counts={summary} />
          </div>
        </div>
      </div>

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
                    <span className="w-full truncate">{l.assigned_to?.email ?? "—"}</span>
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
                      <td className="px-5 py-3 text-muted">{l.assigned_to?.email ?? "—"}</td>
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

function KpiCard({
  label,
  value,
  tone,
  delay,
}: {
  label: string;
  value: number;
  tone?: "danger";
  delay: number;
}) {
  const shown = useCountUp(value);
  return (
    <div
      className={`animate-rise ${card} flex flex-col gap-1 p-4 ${
        tone === "danger" ? "border-overdue/25 bg-overdue-tint" : ""
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
    </div>
  );
}
