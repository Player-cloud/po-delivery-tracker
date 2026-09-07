"use client";

import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { apiFetch } from "@/lib/api";
import StatusBadge from "@/components/StatusBadge";
import { daysRemainingLabel } from "@/lib/urgency";
import { card, h1, input, page } from "@/lib/ui";

type POLine = {
  id: number;
  po_number: string;
  po_line: number;
  promised_delivery: string;
  days_remaining: number;
  status: string;
  delivered: boolean;
  assigned_to: { id: number; email: string } | null;
};

// Values the API's ?status= filter understands (app/models/po_line.py Status).
const STATUS_OPTIONS = ["Upcoming", "Due Today", "Overdue", "Delivered"];

export default function POLinesPage() {
  return (
    <Suspense fallback={<p className={`${page} text-muted`}>Loading…</p>}>
      <POLines />
    </Suspense>
  );
}

function POLines() {
  const focusParam = useSearchParams().get("focus");
  const searchRef = useRef<HTMLInputElement>(null);

  const [lines, setLines] = useState<POLine[]>([]);
  const [error, setError] = useState("");
  const [loadedQuery, setLoadedQuery] = useState<string | null>(null);

  const [status, setStatus] = useState("");
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");

  useEffect(() => {
    if (focusParam) searchRef.current?.focus();
  }, [focusParam]);

  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search.trim()), 300);
    return () => clearTimeout(t);
  }, [search]);

  const query = useMemo(() => {
    const p = new URLSearchParams();
    if (status) p.set("status", status);
    if (debouncedSearch) p.set("search", debouncedSearch);
    const s = p.toString();
    return s ? `?${s}` : "";
  }, [status, debouncedSearch]);

  const loading = loadedQuery !== query;
  const filtered = !!status || !!debouncedSearch;

  useEffect(() => {
    let ignore = false;
    (async () => {
      try {
        const res = await apiFetch(`/po-lines${query}`);
        if (!res.ok) throw new Error();
        const data = await res.json();
        if (!ignore) {
          setLines(data);
          setError("");
        }
      } catch {
        if (!ignore) setError("Could not load PO lines");
      } finally {
        if (!ignore) setLoadedQuery(query);
      }
    })();
    return () => {
      ignore = true;
    };
  }, [query]);

  return (
    <div className={`${page} flex flex-col gap-4`}>
      <div className="flex items-center justify-between">
        <h1 className={h1}>PO Lines</h1>
        <span className="text-[12.5px] text-muted">
          {loading ? "…" : `${lines.length} line${lines.length === 1 ? "" : "s"}`}
        </span>
      </div>

      <div className="flex flex-wrap items-center gap-2.5">
        <div className="flex items-center gap-2 rounded-[var(--radius-control)] border border-line bg-surface px-3 py-2">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-faint" aria-hidden>
            <circle cx="11" cy="11" r="7" />
            <path d="M21 21l-4.3-4.3" />
          </svg>
          <input
            ref={searchRef}
            type="search"
            placeholder="Search PO number…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-44 bg-transparent text-sm outline-none placeholder:text-faint sm:w-56"
            aria-label="Search PO number"
          />
        </div>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className={input}
          aria-label="Filter by status"
        >
          <option value="">All statuses</option>
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        {filtered && (
          <button
            onClick={() => {
              setStatus("");
              setSearch("");
            }}
            className="text-sm text-muted hover:text-ink"
          >
            Clear
          </button>
        )}
      </div>

      {error && <p className="text-overdue-on">{error}</p>}

      {!loading && lines.length === 0 && !error ? (
        <div className={`${card} px-5 py-10 text-center text-sm text-faint`}>
          {filtered ? "No PO lines match." : "No PO lines yet."}
        </div>
      ) : (
        <>
          {/* Phones / small tablets: stacked cards */}
          <ul className="flex flex-col gap-2.5 md:hidden">
            {lines.map((line) => (
              <li key={line.id} className={`${card} flex flex-col gap-2 p-4`}>
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <span className="font-semibold">{line.po_number}</span>
                    <span className="ml-1.5 font-mono text-faint">· {line.po_line}</span>
                  </div>
                  <StatusBadge delivered={line.delivered} days_remaining={line.days_remaining} />
                </div>
                <dl className="grid grid-cols-2 gap-x-3 gap-y-1 text-[12.5px] text-muted">
                  <div>
                    <dt className="text-faint">Promised</dt>
                    <dd className="font-mono">{line.promised_delivery}</dd>
                  </div>
                  <div>
                    <dt className="text-faint">Remaining</dt>
                    <dd>{line.delivered ? "—" : daysRemainingLabel(line.days_remaining)}</dd>
                  </div>
                  <div className="col-span-2">
                    <dt className="text-faint">Assignee</dt>
                    <dd className="truncate">{line.assigned_to?.email ?? "—"}</dd>
                  </div>
                </dl>
                <div className="flex gap-4 pt-1 text-[12.5px]">
                  <Link href={`/po-lines/edit?id=${line.id}`} className="text-accent hover:underline">
                    Edit
                  </Link>
                  <Link
                    href={`/po-lines/request-deletion?id=${line.id}`}
                    className="text-overdue-on hover:underline"
                  >
                    Request deletion
                  </Link>
                </div>
              </li>
            ))}
          </ul>

          {/* Tablet landscape and up: table */}
          <div className={`${card} hidden overflow-hidden md:block`}>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px] text-left text-[12.5px]">
                <thead>
                  <tr className="border-b border-line text-[10.5px] uppercase tracking-[0.04em] text-faint">
                    <th className="px-5 py-3 font-medium">PO Number</th>
                    <th className="px-5 py-3 font-medium">Line</th>
                    <th className="px-5 py-3 font-medium">Promised</th>
                    <th className="px-5 py-3 font-medium">Remaining</th>
                    <th className="px-5 py-3 font-medium">Assignee</th>
                    <th className="px-5 py-3 font-medium">Status</th>
                    <th className="px-5 py-3" />
                  </tr>
                </thead>
                <tbody>
                  {lines.map((line) => (
                    <tr key={line.id} className="border-t border-line/70 hover:bg-surface-tint">
                      <td className="px-5 py-3 font-semibold">{line.po_number}</td>
                      <td className="px-5 py-3 font-mono">{line.po_line}</td>
                      <td className="px-5 py-3 font-mono text-muted">{line.promised_delivery}</td>
                      <td className="px-5 py-3 text-muted">
                        {line.delivered ? "—" : daysRemainingLabel(line.days_remaining)}
                      </td>
                      <td className="px-5 py-3 text-muted">{line.assigned_to?.email ?? "—"}</td>
                      <td className="px-5 py-3">
                        <StatusBadge delivered={line.delivered} days_remaining={line.days_remaining} />
                      </td>
                      <td className="whitespace-nowrap px-5 py-3">
                        <Link href={`/po-lines/edit?id=${line.id}`} className="text-accent hover:underline">
                          Edit
                        </Link>
                        <span className="text-line"> · </span>
                        <Link
                          href={`/po-lines/request-deletion?id=${line.id}`}
                          className="text-overdue-on hover:underline"
                        >
                          Request deletion
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
