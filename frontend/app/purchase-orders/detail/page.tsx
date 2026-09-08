"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { extractErrorMessage } from "@/lib/errors";
import { DeliveryPill, POStatusPill } from "@/components/Pill";
import StatusBadge from "@/components/StatusBadge";
import { assigneeLabel } from "@/lib/status";
import { daysRemainingLabel } from "@/lib/urgency";
import { useAuth } from "@/lib/useAuth";
import { btnGhost, btnPrimary, card, h1, page } from "@/lib/ui";
import type { PurchaseOrderDetail } from "@/lib/types";

type Action = "close" | "cancel" | "reopen";

export default function PurchaseOrderDetailPage() {
  return (
    <Suspense fallback={<p className="mx-auto max-w-3xl p-6 text-muted">Loading…</p>}>
      <Detail />
    </Suspense>
  );
}

function Detail() {
  const id = useSearchParams().get("id");
  const { role } = useAuth();
  const canManage = role === "administrator" || role === "manager";

  const [po, setPO] = useState<PurchaseOrderDetail | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!id) return;
    let ignore = false;
    (async () => {
      try {
        const res = await apiFetch(`/purchase-orders/${id}`);
        if (!res.ok) throw new Error();
        const data = await res.json();
        if (!ignore) setPO(data);
      } catch {
        if (!ignore) setError("Could not load this purchase order");
      }
    })();
    return () => {
      ignore = true;
    };
  }, [id]);

  async function act(action: Action) {
    setBusy(true);
    setError("");
    const res = await apiFetch(`/purchase-orders/${id}`, {
      method: "PUT",
      body: JSON.stringify({ action }),
    });
    setBusy(false);
    if (!res.ok) {
      setError(extractErrorMessage(await res.json().catch(() => ({}))));
      return;
    }
    setPO(await res.json());
  }

  if (!id) return <p className="mx-auto max-w-3xl p-6 text-overdue-on">No PO specified.</p>;
  if (error && !po) return <p className="mx-auto max-w-3xl p-6 text-overdue-on">{error}</p>;
  if (!po) return <p className="mx-auto max-w-3xl p-6 text-muted">Loading…</p>;

  const canClose = po.status === "delivered";
  const canCancel = po.status === "open" || po.status === "delivered";
  const canReopen = po.status === "closed" || po.status === "cancelled";

  return (
    <div className={`${page} flex flex-col gap-5`}>
      <div>
        <Link href="/purchase-orders" className="text-[12.5px] text-accent hover:underline">
          ← All purchase orders
        </Link>
        <div className="mt-1 flex flex-wrap items-center gap-3">
          <h1 className={h1}>PO {po.po_number}</h1>
          <POStatusPill status={po.status} />
          <span className="text-[12.5px] text-muted">
            {po.lines_complete}/{po.line_count} lines complete
          </span>
        </div>
      </div>

      {canManage && (canClose || canCancel || canReopen) && (
        <div className="flex flex-wrap gap-2">
          {canClose && (
            <button onClick={() => act("close")} disabled={busy} className={btnPrimary}>
              Close PO
            </button>
          )}
          {canCancel && (
            <button
              onClick={() => act("cancel")}
              disabled={busy}
              className="inline-flex items-center justify-center rounded-[var(--radius-control)] border border-overdue/40 bg-surface px-4 py-2 text-sm font-medium text-overdue-on transition-colors hover:bg-overdue-tint disabled:opacity-50"
            >
              Cancel PO
            </button>
          )}
          {canReopen && (
            <button onClick={() => act("reopen")} disabled={busy} className={btnGhost}>
              Reopen PO
            </button>
          )}
        </div>
      )}

      {error && <p className="text-sm text-overdue-on">{error}</p>}

      <div className="flex items-center justify-between">
        <h2 className="font-display text-[15px] font-semibold">Lines</h2>
        {po.status !== "closed" && po.status !== "cancelled" && (
          <Link
            href={`/po-lines/new?po=${encodeURIComponent(po.po_number)}`}
            className="text-[12.5px] text-accent hover:underline"
          >
            + Add line
          </Link>
        )}
      </div>

      {po.lines.length === 0 ? (
        <div className={`${card} px-5 py-8 text-center text-sm text-faint`}>No lines on this PO yet.</div>
      ) : (
        <>
          {/* Phones: cards */}
          <ul className="flex flex-col gap-2.5 md:hidden">
            {po.lines.map((l) => (
              <li key={l.id} className={`${card} flex flex-col gap-2 p-4`}>
                <div className="flex items-center justify-between gap-3">
                  <span className="font-semibold">Line {l.po_line}</span>
                  <DeliveryPill status={l.delivery_status} />
                </div>
                <dl className="grid grid-cols-2 gap-x-3 gap-y-1 text-[12.5px] text-muted">
                  <div>
                    <dt className="text-faint">Promised</dt>
                    <dd className="font-mono">{l.promised_delivery}</dd>
                  </div>
                  <div>
                    <dt className="text-faint">Remaining</dt>
                    <dd>{l.delivered ? "—" : daysRemainingLabel(l.days_remaining)}</dd>
                  </div>
                  <div className="col-span-2">
                    <dt className="text-faint">Assignee</dt>
                    <dd className="truncate">{assigneeLabel(l.assigned_to)}</dd>
                  </div>
                </dl>
                <Link href={`/po-lines/edit?id=${l.id}`} className="text-[12.5px] text-accent hover:underline">
                  Edit
                </Link>
              </li>
            ))}
          </ul>

          {/* Tablet+ : table */}
          <div className={`${card} hidden overflow-hidden md:block`}>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[600px] text-left text-[12.5px]">
                <thead>
                  <tr className="border-b border-line text-[10.5px] uppercase tracking-[0.04em] text-faint">
                    <th className="px-5 py-3 font-medium">Line</th>
                    <th className="px-5 py-3 font-medium">Promised</th>
                    <th className="px-5 py-3 font-medium">Remaining</th>
                    <th className="px-5 py-3 font-medium">Delivery</th>
                    <th className="px-5 py-3 font-medium">Urgency</th>
                    <th className="px-5 py-3 font-medium">Assignee</th>
                    <th className="px-5 py-3" />
                  </tr>
                </thead>
                <tbody>
                  {po.lines.map((l) => (
                    <tr key={l.id} className="border-t border-line/70 hover:bg-surface-tint">
                      <td className="px-5 py-3 font-mono font-semibold">{l.po_line}</td>
                      <td className="px-5 py-3 font-mono text-muted">{l.promised_delivery}</td>
                      <td className="px-5 py-3 text-muted">
                        {l.delivered ? "—" : daysRemainingLabel(l.days_remaining)}
                      </td>
                      <td className="px-5 py-3">
                        <DeliveryPill status={l.delivery_status} />
                      </td>
                      <td className="px-5 py-3">
                        <StatusBadge delivered={l.delivered} days_remaining={l.days_remaining} />
                      </td>
                      <td className="px-5 py-3 text-muted">{assigneeLabel(l.assigned_to)}</td>
                      <td className="px-5 py-3">
                        <Link href={`/po-lines/edit?id=${l.id}`} className="text-accent hover:underline">
                          Edit
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
