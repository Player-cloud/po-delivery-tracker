"use client";

import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "@/lib/api";
import { assigneeLabel } from "@/lib/status";
import { btnGhost, btnPrimary, card, h1, input, page } from "@/lib/ui";
import type { AssignableUser } from "@/lib/types";

type ReportMeta = { name: string; label: string; description: string };
type Column = { key: string; label: string };
type ReportData = {
  label: string;
  columns: Column[];
  rows: Record<string, string | number>[];
  summary: Record<string, string | number | null> | null;
};

type Filters = {
  from: string;
  to: string;
  assignee_id: string;
  po: string;
  priority: string;
  delivery_status: string;
  po_status: string;
};

const EMPTY: Filters = {
  from: "",
  to: "",
  assignee_id: "",
  po: "",
  priority: "",
  delivery_status: "",
  po_status: "",
};

const REPORTS: ReportMeta[] = [
  { name: "all_lines", label: "All PO lines", description: "Every line in the system — filter it however you like, or not at all." },
  { name: "overdue", label: "Overdue lines", description: "Every open line past its promised date." },
  { name: "delivered", label: "Deliveries", description: "Lines completed within a date range." },
  { name: "on_time", label: "On-time delivery", description: "On-time vs late completions, by assignee." },
  { name: "by_assignee", label: "Lines by assignee", description: "Line counts per person, by delivery status." },
  { name: "by_status", label: "Lines by delivery status", description: "How lines split across delivery states." },
];

function queryFrom(f: Filters): string {
  const p = new URLSearchParams();
  if (f.from) p.set("from", f.from);
  if (f.to) p.set("to", f.to);
  if (f.assignee_id) p.set("assignee_id", f.assignee_id);
  if (f.po) p.set("po", f.po);
  if (f.priority) p.set("priority", f.priority);
  if (f.delivery_status) p.set("delivery_status", f.delivery_status);
  if (f.po_status) p.set("po_status", f.po_status);
  return p.toString();
}

export default function ReportsPage() {
  const [name, setName] = useState("all_lines");
  const [draft, setDraft] = useState<Filters>(EMPTY);
  const [applied, setApplied] = useState<Filters>(EMPTY);
  const [users, setUsers] = useState<AssignableUser[]>([]);
  const [data, setData] = useState<ReportData | null>(null);
  const [error, setError] = useState("");
  const [loadedKey, setLoadedKey] = useState<string | null>(null);
  const [downloading, setDownloading] = useState("");

  const meta = REPORTS.find((r) => r.name === name)!;
  const query = useMemo(() => queryFrom(applied), [applied]);
  const key = `${name}|${query}`;
  const loading = loadedKey !== key;

  useEffect(() => {
    let ignore = false;
    (async () => {
      try {
        const res = await apiFetch("/users/assignable");
        if (res.ok && !ignore) setUsers(await res.json());
      } catch {
        /* picker just stays empty */
      }
    })();
    return () => {
      ignore = true;
    };
  }, []);

  useEffect(() => {
    let ignore = false;
    (async () => {
      try {
        const q = query ? `?${query}` : "";
        const res = await apiFetch(`/reports/${name}${q}`);
        if (!res.ok) throw new Error();
        const d = await res.json();
        if (!ignore) {
          setData(d);
          setError("");
        }
      } catch {
        if (!ignore) setError("Could not run this report");
      } finally {
        if (!ignore) setLoadedKey(`${name}|${query}`);
      }
    })();
    return () => {
      ignore = true;
    };
  }, [name, query]);

  async function download(fmt: "csv" | "xlsx" | "pdf") {
    setDownloading(fmt);
    try {
      const q = query ? `?${query}&format=${fmt}` : `?format=${fmt}`;
      const res = await apiFetch(`/reports/${name}${q}`);
      if (!res.ok) throw new Error();
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${name}.${fmt}`;
      link.click();
      URL.revokeObjectURL(url);
    } catch {
      setError("Download failed");
    } finally {
      setDownloading("");
    }
  }

  function setDraftField<K extends keyof Filters>(k: K, v: Filters[K]) {
    setDraft((prev) => ({ ...prev, [k]: v }));
  }

  const filtersDirty = JSON.stringify(draft) !== JSON.stringify(applied);

  return (
    <div className={`${page} flex flex-col gap-5`}>
      <div>
        <h1 className={h1}>Reports</h1>
        <p className="mt-1 text-sm text-muted">{meta.description}</p>
      </div>

      <div className="flex flex-wrap gap-2">
        {REPORTS.map((r) => (
          <button
            key={r.name}
            onClick={() => setName(r.name)}
            aria-pressed={r.name === name}
            className={`rounded-full px-3 py-1.5 text-[13px] font-medium transition-colors ${
              r.name === name
                ? "bg-accent-soft text-accent-hover"
                : "border border-line text-muted hover:text-ink"
            }`}
          >
            {r.label}
          </button>
        ))}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          setApplied(draft);
        }}
        className={`${card} flex flex-wrap items-end gap-3 p-4`}
      >
        <label className="flex flex-col gap-1 text-xs text-muted">
          From
          <input
            type="date"
            value={draft.from}
            onChange={(e) => setDraftField("from", e.target.value)}
            className={input}
          />
        </label>
        <label className="flex flex-col gap-1 text-xs text-muted">
          To
          <input
            type="date"
            value={draft.to}
            onChange={(e) => setDraftField("to", e.target.value)}
            className={input}
          />
        </label>
        <label className="flex flex-col gap-1 text-xs text-muted">
          Assignee
          <select
            value={draft.assignee_id}
            onChange={(e) => setDraftField("assignee_id", e.target.value)}
            className={input}
          >
            <option value="">Anyone</option>
            {users.map((u) => (
              <option key={u.id} value={String(u.id)}>
                {assigneeLabel(u)}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-muted">
          PO number
          <input
            value={draft.po}
            onChange={(e) => setDraftField("po", e.target.value)}
            className={input}
            placeholder="contains…"
          />
        </label>
        <label className="flex flex-col gap-1 text-xs text-muted">
          Priority
          <select
            value={draft.priority}
            onChange={(e) => setDraftField("priority", e.target.value)}
            className={input}
          >
            <option value="">Any</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-muted">
          Delivery
          <select
            value={draft.delivery_status}
            onChange={(e) => setDraftField("delivery_status", e.target.value)}
            className={input}
          >
            <option value="">Any</option>
            <option value="not_delivered">Not delivered</option>
            <option value="partial">Partial</option>
            <option value="complete">Complete</option>
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-muted">
          PO status
          <select
            value={draft.po_status}
            onChange={(e) => setDraftField("po_status", e.target.value)}
            className={input}
          >
            <option value="">Any</option>
            <option value="open">Pending</option>
            <option value="delivered">Delivered</option>
            <option value="closed">Closed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </label>
        <button type="submit" disabled={!filtersDirty} className={btnPrimary}>
          Apply
        </button>
        <button
          type="button"
          onClick={() => {
            setDraft(EMPTY);
            setApplied(EMPTY);
          }}
          disabled={!filtersDirty && !query}
          className={btnGhost}
        >
          Clear filters
        </button>
      </form>

      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs text-muted">Download:</span>
        {(["csv", "xlsx", "pdf"] as const).map((fmt) => (
          <button
            key={fmt}
            onClick={() => download(fmt)}
            disabled={!!downloading || loading || !!error}
            className="rounded-[var(--radius-control)] border border-line bg-surface px-3 py-1.5 text-xs font-medium transition-colors hover:bg-page disabled:opacity-50"
          >
            {downloading === fmt ? "…" : fmt === "xlsx" ? "Excel" : fmt.toUpperCase()}
          </button>
        ))}
      </div>

      {error && <p className="text-sm text-overdue-on">{error}</p>}

      {data && Array.isArray(data.columns) && (
        <div className={`${card} overflow-hidden`}>
          {data.summary && (
            <div className="flex flex-wrap gap-x-6 gap-y-1 border-b border-line px-5 py-3 text-[12.5px]">
              {Object.entries(data.summary).map(([k, v]) => (
                <span key={k}>
                  <span className="text-faint">{k.replace(/_/g, " ")}: </span>
                  <span className="font-semibold">{v ?? "—"}</span>
                </span>
              ))}
            </div>
          )}
          <div className="overflow-x-auto">
            <table className="w-full min-w-[560px] text-left text-[12.5px]">
              <thead>
                <tr className="border-b border-line text-[10.5px] uppercase tracking-[0.04em] text-faint">
                  {data.columns.map((c) => (
                    <th key={c.key} className="px-5 py-3 font-medium">
                      {c.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.rows.map((row, i) => (
                  <tr key={i} className="border-t border-line/70">
                    {data.columns.map((c) => (
                      <td key={c.key} className="px-5 py-2.5">
                        {row[c.key] ?? "—"}
                      </td>
                    ))}
                  </tr>
                ))}
                {data.rows.length === 0 && (
                  <tr>
                    <td
                      colSpan={data.columns.length}
                      className="px-5 py-10 text-center text-faint"
                    >
                      {loading ? "Running…" : "Nothing to report."}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
