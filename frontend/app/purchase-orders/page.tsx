"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { extractErrorMessage } from "@/lib/errors";
import { POStatusPill } from "@/components/Pill";
import { btnGhost, btnPrimary, card, h1, input, page } from "@/lib/ui";
import type { PurchaseOrder, PurchaseOrderStatus } from "@/lib/types";

const STATUSES: PurchaseOrderStatus[] = ["open", "delivered", "closed", "cancelled"];

export default function PurchaseOrdersPage() {
  return (
    <Suspense fallback={<p className={`${page} text-muted`}>Loading…</p>}>
      <PurchaseOrders />
    </Suspense>
  );
}

function PurchaseOrders() {
  const router = useRouter();
  const statusParam = useSearchParams().get("status") ?? "";

  const [pos, setPOs] = useState<PurchaseOrder[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);
  const [newNumber, setNewNumber] = useState("");
  const [showCreate, setShowCreate] = useState(false);

  const [status, setStatus] = useState(statusParam);

  const query = useMemo(() => (status ? `?status=${encodeURIComponent(status)}` : ""), [status]);

  useEffect(() => {
    let ignore = false;
    (async () => {
      try {
        const res = await apiFetch(`/purchase-orders${query}`);
        if (!res.ok) throw new Error();
        const data = await res.json();
        if (!ignore) {
          setPOs(data);
          setError("");
        }
      } catch {
        if (!ignore) setError("Could not load purchase orders");
      } finally {
        if (!ignore) setLoaded(true);
      }
    })();
    return () => {
      ignore = true;
    };
  }, [query]);

  async function createPO(e: React.FormEvent) {
    e.preventDefault();
    setCreating(true);
    setError("");
    const res = await apiFetch("/purchase-orders", {
      method: "POST",
      body: JSON.stringify({ po_number: newNumber.trim() }),
    });
    setCreating(false);
    if (!res.ok) {
      setError(extractErrorMessage(await res.json().catch(() => ({})), "Could not create PO"));
      return;
    }
    const po = await res.json();
    router.push(`/purchase-orders/detail?id=${po.id}`);
  }

  return (
    <div className={`${page} flex flex-col gap-4`}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className={h1}>Purchase Orders</h1>
        <button onClick={() => setShowCreate((v) => !v)} className={btnGhost}>
          {showCreate ? "Cancel" : "+ New PO"}
        </button>
      </div>

      {showCreate && (
        <form onSubmit={createPO} className={`${card} flex flex-wrap items-end gap-3 p-4`}>
          <label className="flex flex-1 flex-col gap-1 text-sm">
            <span className="font-medium text-muted">PO number</span>
            <input
              value={newNumber}
              onChange={(e) => setNewNumber(e.target.value)}
              className={input}
              placeholder="e.g. 4500123"
              required
              autoFocus
            />
          </label>
          <button type="submit" disabled={creating} className={btnPrimary}>
            {creating ? "Creating…" : "Create"}
          </button>
        </form>
      )}

      <div className="flex flex-wrap items-center gap-2.5">
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className={input}
          aria-label="Filter by status"
        >
          <option value="">All statuses</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s[0].toUpperCase() + s.slice(1)}
            </option>
          ))}
        </select>
        {status && (
          <button onClick={() => setStatus("")} className="text-sm text-muted hover:text-ink">
            Clear
          </button>
        )}
        <span className="ml-auto text-[12.5px] text-muted">
          {loaded ? `${pos.length} PO${pos.length === 1 ? "" : "s"}` : "…"}
        </span>
      </div>

      {error && <p className="text-sm text-overdue-on">{error}</p>}

      {loaded && pos.length === 0 && !error ? (
        <div className={`${card} px-5 py-10 text-center text-sm text-faint`}>
          {status ? "No purchase orders match." : "No purchase orders yet."}
        </div>
      ) : (
        <>
          {/* Phones: cards */}
          <ul className="flex flex-col gap-2.5 md:hidden">
            {pos.map((po) => (
              <li key={po.id}>
                <Link href={`/purchase-orders/detail?id=${po.id}`} className={`${card} flex flex-col gap-2 p-4`}>
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-semibold">{po.po_number}</span>
                    <POStatusPill status={po.status} />
                  </div>
                  <span className="text-[12.5px] text-muted">
                    {po.lines_complete}/{po.line_count} lines complete · created{" "}
                    {po.created_at.slice(0, 10)}
                  </span>
                </Link>
              </li>
            ))}
          </ul>

          {/* Tablet+ : table */}
          <div className={`${card} hidden overflow-hidden md:block`}>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[560px] text-left text-[12.5px]">
                <thead>
                  <tr className="border-b border-line text-[10.5px] uppercase tracking-[0.04em] text-faint">
                    <th className="px-5 py-3 font-medium">PO Number</th>
                    <th className="px-5 py-3 font-medium">Status</th>
                    <th className="px-5 py-3 font-medium">Lines</th>
                    <th className="px-5 py-3 font-medium">Created</th>
                  </tr>
                </thead>
                <tbody>
                  {pos.map((po) => (
                    <tr
                      key={po.id}
                      onClick={() => router.push(`/purchase-orders/detail?id=${po.id}`)}
                      className="cursor-pointer border-t border-line/70 hover:bg-surface-tint"
                    >
                      <td className="px-5 py-3 font-semibold">
                        <Link
                          href={`/purchase-orders/detail?id=${po.id}`}
                          className="hover:text-accent"
                          onClick={(e) => e.stopPropagation()}
                        >
                          {po.po_number}
                        </Link>
                      </td>
                      <td className="px-5 py-3">
                        <POStatusPill status={po.status} />
                      </td>
                      <td className="px-5 py-3 text-muted">
                        {po.lines_complete}/{po.line_count}
                      </td>
                      <td className="px-5 py-3 font-mono text-muted">{po.created_at.slice(0, 10)}</td>
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
