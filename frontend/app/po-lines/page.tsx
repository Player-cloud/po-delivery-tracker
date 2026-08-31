"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import StatusBadge from "@/components/StatusBadge";
import { daysRemainingLabel } from "@/lib/urgency";

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
  const [lines, setLines] = useState<POLine[]>([]);
  const [error, setError] = useState("");
  // `loading` is derived: true whenever the fetched data isn't for the current query.
  const [loadedQuery, setLoadedQuery] = useState<string | null>(null);

  const [status, setStatus] = useState("");
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");

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
    <div className="p-8">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">PO Lines</h1>
        <Link
          href="/po-lines/new"
          className="rounded bg-black px-4 py-2 text-white hover:bg-zinc-800"
        >
          New PO Line
        </Link>
      </div>

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <input
          type="search"
          placeholder="Search PO number..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-64 rounded border px-3 py-2 text-sm"
        />
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="rounded border px-3 py-2 text-sm"
        >
          <option value="">All statuses</option>
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        {(status || debouncedSearch) && (
          <button
            onClick={() => {
              setStatus("");
              setSearch("");
            }}
            className="text-sm text-zinc-500 hover:text-black"
          >
            Clear
          </button>
        )}
        <span className="ml-auto text-sm text-zinc-400">
          {loading ? "Loading..." : `${lines.length} line${lines.length === 1 ? "" : "s"}`}
        </span>
      </div>

      {error && <p className="text-red-600">{error}</p>}

      <table className="w-full border-collapse text-left text-sm">
        <thead>
          <tr className="border-b text-xs uppercase text-zinc-400">
            <th className="py-2 font-medium">PO Number</th>
            <th className="font-medium">Line</th>
            <th className="font-medium">Promised Delivery</th>
            <th className="font-medium">Remaining</th>
            <th className="font-medium">Assigned</th>
            <th className="font-medium">Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {lines.map((line) => (
            <tr key={line.id} className="border-b">
              <td className="py-2 font-medium">{line.po_number}</td>
              <td>{line.po_line}</td>
              <td className="tabular-nums text-zinc-600">{line.promised_delivery}</td>
              <td className="tabular-nums text-zinc-600">
                {line.delivered ? "—" : daysRemainingLabel(line.days_remaining)}
              </td>
              <td className="text-zinc-600">{line.assigned_to?.email ?? "—"}</td>
              <td>
                <StatusBadge
                  delivered={line.delivered}
                  days_remaining={line.days_remaining}
                />
              </td>
              <td className="whitespace-nowrap">
                <Link
                  href={`/po-lines/${line.id}/edit`}
                  className="text-blue-600 hover:underline"
                >
                  Edit
                </Link>
                {" · "}
                <Link
                  href={`/po-lines/${line.id}/edit/request-deletion`}
                  className="text-red-600 hover:underline"
                >
                  Request Deletion
                </Link>
              </td>
            </tr>
          ))}
          {!loading && lines.length === 0 && !error && (
            <tr>
              <td colSpan={7} className="py-8 text-center text-zinc-400">
                No PO lines match.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
