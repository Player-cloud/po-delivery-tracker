"use client";

import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { apiFetch } from "@/lib/api";
import StatusBadge from "@/components/StatusBadge";
import { DeliveryPill } from "@/components/Pill";
import { assigneeLabel } from "@/lib/status";
import { daysRemainingLabel } from "@/lib/urgency";
import { card, h1, input, page } from "@/lib/ui";
import type { POLine } from "@/lib/types";

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
  const params = useSearchParams();
  const focusParam = params.get("focus");
  // Drill-through params set by the dashboard cards (no UI control of their own).
  const dueWithin = params.get("due_within");
  const deliveryStatusParam = params.get("delivery_status");
  const priorityParam = params.get("priority");
  const searchRef = useRef<HTMLInputElement>(null);

  const [lines, setLines] = useState<POLine[]>([]);
  const [error, setError] = useState("");
  const [loadedQuery, setLoadedQuery] = useState<string | null>(null);

  const [status, setStatus] = useState(params.get("status") ?? "");
  const [poStatus, setPoStatus] = useState(params.get("po_status") ?? "");
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
    if (poStatus) p.set("po_status", poStatus);
    if (debouncedSearch) p.set("search", debouncedSearch);
    if (dueWithin) p.set("due_within", dueWithin);
    if (deliveryStatusParam) p.set("delivery_status", deliveryStatusParam);
    if (priorityParam) p.set("priority", priorityParam);
    const s = p.toString();
    return s ? `?${s}` : "";
  }, [status, poStatus, debouncedSearch, dueWithin, deliveryStatusParam, priorityParam]);

  const loading = loadedQuery !== query;
  const drilled = !!dueWithin || !!deliveryStatusParam || !!priorityParam;
  const filtered = !!status || !!poStatus || !!debouncedSearch || drilled;

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

  const drillLabel = dueWithin
    ? `Due in 1–${dueWithin} days`
    : deliveryStatusParam
      ? `Delivery: ${deliveryStatusParam.replace("_", " ")}`
      : priorityParam
        ? `Priority: ${priorityParam}`
        : "";

  return (
    <div className={`${page} flex flex-col gap-4`}>
      <div className="flex items-center justify-between">
        <h1 className={h1}>PO Lines</h1>
        <span className="text-[12.5px] text-muted">
          {loading ? "…" : `${lines.length} line${lines.length === 1 ? "" : "s"}`}
        </span>
      </div>

      {drilled && (
        <div className="flex items-center gap-2 text-[12.5px]">
          <span className="rounded-full bg-accent-soft px-2.5 py-0.5 font-medium text-accent-hover">
            {drillLabel}
          </span>
          <Link href="/po-lines" className="text-muted hover:text-ink">
            Clear
          </Link>
        </div>
      )}

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
          aria-label="Filter by urgency"
        >
          <option value="">All statuses</option>
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <select
          value={poStatus}
          onChange={(e) => setPoStatus(e.target.value)}
          className={input}
          aria-label="Filter by PO status"
        >
          <option value="">Any PO status</option>
          <option value="open">Pending PO</option>
          <option value="delivered">Delivered PO</option>
          <option value="closed">Closed PO</option>
          <option value="cancelled">Cancelled PO</option>
        </select>
        {(status || poStatus || search) && (
          <button
            onClick={() => {
              setStatus("");
              setPoStatus("");
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
                    {line.description && (
                      <p className="truncate text-[12.5px] text-muted">{line.description}</p>
                    )}
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
                  <div>
                    <dt className="text-faint">Delivery</dt>
                    <dd>
                      <DeliveryPill status={line.delivery_status} />
                    </dd>
                  </div>
                  <div className="col-span-2">
                    <dt className="text-faint">Assignee</dt>
                    <dd className="truncate">{assigneeLabel(line.assigned_to)}</dd>
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
              <table className="w-full min-w-[780px] text-left text-[12.5px]">
                <thead>
                  <tr className="border-b border-line text-[10.5px] uppercase tracking-[0.04em] text-faint">
                    <th className="px-5 py-3 font-medium">PO Number</th>
                    <th className="px-5 py-3 font-medium">Line</th>
                    <th className="px-5 py-3 font-medium">Description</th>
                    <th className="px-5 py-3 font-medium">Promised</th>
                    <th className="px-5 py-3 font-medium">Remaining</th>
                    <th className="px-5 py-3 font-medium">Delivery</th>
                    <th className="px-5 py-3 font-medium">Assignee</th>
                    <th className="px-5 py-3 font-medium">Status</th>
                    <th className="px-5 py-3" />
                  </tr>
                </thead>
                <tbody>
                  {lines.map((line) => (
                    <tr key={line.id} className="border-t border-line/70 hover:bg-surface-tint">
                      <td className="px-5 py-3 font-semibold">
                        <Link
                          href={`/purchase-orders/detail?id=${line.purchase_order_id}`}
                          className="hover:text-accent"
                        >
                          {line.po_number}
                        </Link>
                      </td>
                      <td className="px-5 py-3 font-mono">{line.po_line}</td>
                      <td className="max-w-[220px] truncate px-5 py-3 text-muted">
                        {line.description || "—"}
                      </td>
                      <td className="px-5 py-3 font-mono text-muted">{line.promised_delivery}</td>
                      <td className="px-5 py-3 text-muted">
                        {line.delivered ? "—" : daysRemainingLabel(line.days_remaining)}
                      </td>
                      <td className="px-5 py-3">
                        <DeliveryPill status={line.delivery_status} />
                      </td>
                      <td className="px-5 py-3 text-muted">{assigneeLabel(line.assigned_to)}</td>
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
