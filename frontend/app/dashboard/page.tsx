"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

type DashboardSummary = {
  total_open: number;
  due_today: number;
  due_this_week: number;
  overdue: number;
  completed: number;
  high_priority: number;
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
  const [error, setError] = useState("");

  useEffect(() => {
    apiFetch("/dashboard/summary")
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load dashboard");
        return res.json();
      })
      .then((data) => setSummary(data))
      .catch(() => setError("Could not load dashboard"));
  }, []);

  if (error) return <p className="p-8 text-red-600">{error}</p>;
  if (!summary) return <p className="p-8">Loading...</p>;

  return (
    <div className="p-8">
      <h1 className="mb-6 text-xl font-semibold">Dashboard</h1>
      <div className="grid grid-cols-3 gap-4">
        {CARDS.map((card) => (
          <div
            key={card.key}
            className={`rounded border-t-4 bg-white p-6 shadow ${card.accent}`}
          >
            <p className="text-3xl font-bold">{summary[card.key]}</p>
            <p className="text-sm text-zinc-600">{card.label}</p>
          </div>
        ))}
      </div>
    </div>
  );
}