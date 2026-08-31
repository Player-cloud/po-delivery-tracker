"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import StatusBadge from "@/components/StatusBadge";
import UrgencyBar from "@/components/UrgencyBar";
import { daysRemainingLabel } from "@/lib/urgency";

type DashboardSummary = {
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
  priority: string | null;
  assigned_to: { id: number; email: string } | null;
};

const CARDS: { key: keyof DashboardSummary; label: string; accent: string }[] = [
  { key: "total_open", label: "Total Open Lines", accent: "border-t-blue-500" },
  { key: "due_today", label: "Due Today", accent: "border-t-orange-500" },
  { key: "due_this_week", label: "Due This Week", accent: "border-t-yellow-500" },
  { key: "overdue", label: "Overdue", accent: "border-t-red-500" },
  { key: "completed", label: "Completed", accent: "border-t-green-500" },
  { key: "high_priority", label: "High Priority", accent: "border-t-red-800" },
];

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [attention, setAttention] = useState<AttentionLine[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      apiFetch("/dashboard/summary").then((r) => {
        if (!r.ok) throw new Error();
        return r.json();
      }),
      apiFetch("/dashboard/attention").then((r) => {
        if (!r.ok) throw new Error();
        return r.json();
      }),
    ])
      .then(([s, a]) => {
        setSummary(s);
        setAttention(a);
      })
      .catch(() => setError("Could not load dashboard"));
  }, []);

  if (error) return <p className="p-8 text-red-600">{error}</p>;
  if (!summary || !attention) return <p className="p-8">Loading...</p>;

  return (
    <div className="p-8">
      <h1 className="mb-6 text-xl font-semibold">Dashboard</h1>

      <div className="grid grid-cols-3 gap-4">
        {CARDS.map((card) => (
          <div
            key={card.key}
            className={`rounded border-t-4 bg-white p-6 shadow ${card.accent}`}
          >
            <p className="text-3xl font-bold tabular-nums">{summary[card.key]}</p>
            <p className="text-sm text-zinc-600">{card.label}</p>
          </div>
        ))}
      </div>

      <div className="mt-6">
        <UrgencyBar counts={summary} />
      </div>

      <div className="mt-6 rounded border bg-white shadow">
        <div className="flex items-center justify-between border-b px-6 py-4">
          <h2 className="text-sm font-medium text-zinc-600">
            Needs attention
            <span className="ml-2 text-zinc-400">
              (overdue or due within 7 days)
            </span>
          </h2>
          <Link href="/po-lines" className="text-sm text-blue-600 hover:underline">
            All PO lines
          </Link>
        </div>

        {attention.length === 0 ? (
          <p className="px-6 py-8 text-sm text-zinc-500">
            Nothing needs attention right now.
          </p>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase text-zinc-400">
              <tr className="border-b">
                <th className="px-6 py-2 font-medium">PO / Line</th>
                <th className="px-6 py-2 font-medium">Promised</th>
                <th className="px-6 py-2 font-medium">Remaining</th>
                <th className="px-6 py-2 font-medium">Assigned</th>
                <th className="px-6 py-2 font-medium">Status</th>
                <th className="px-6 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {attention.map((l) => (
                <tr key={l.id} className="border-b last:border-0">
                  <td className="px-6 py-2 font-medium">
                    {l.po_number}
                    <span className="text-zinc-400"> · {l.po_line}</span>
                  </td>
                  <td className="px-6 py-2 tabular-nums text-zinc-600">
                    {l.promised_delivery}
                  </td>
                  <td className="px-6 py-2 tabular-nums text-zinc-600">
                    {daysRemainingLabel(l.days_remaining)}
                  </td>
                  <td className="px-6 py-2 text-zinc-600">
                    {l.assigned_to?.email ?? "—"}
                  </td>
                  <td className="px-6 py-2">
                    <StatusBadge
                      delivered={l.delivered}
                      days_remaining={l.days_remaining}
                    />
                  </td>
                  <td className="px-6 py-2">
                    <Link
                      href={`/po-lines/${l.id}/edit`}
                      className="text-blue-600 hover:underline"
                    >
                      Edit
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
