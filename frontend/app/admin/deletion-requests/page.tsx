"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import RequireAdmin from "@/components/RequireAdmin";
import { card, h1, page } from "@/lib/ui";

type DeletionRequest = {
  id: number;
  po_number: string;
  po_line: number;
  reason: string;
  status: "pending" | "approved" | "rejected";
  requested_by: { email: string };
  reviewed_by: { email: string } | null;
  resolution_notes: string | null;
  created_at: string;
};

export default function DeletionRequestsPage() {
  return (
    <RequireAdmin>
      <DeletionRequests />
    </RequireAdmin>
  );
}

function DeletionRequests() {
  const [requests, setRequests] = useState<DeletionRequest[]>([]);
  const [error, setError] = useState("");
  const [loaded, setLoaded] = useState(false);

  async function reload() {
    try {
      const res = await apiFetch("/deletion-requests");
      if (res.ok) setRequests(await res.json());
      else setError("Could not load deletion requests");
    } catch {
      setError("Could not load deletion requests");
    }
  }

  useEffect(() => {
    let ignore = false;
    (async () => {
      try {
        const res = await apiFetch("/deletion-requests");
        if (!res.ok) throw new Error();
        const data = await res.json();
        if (!ignore) setRequests(data);
      } catch {
        if (!ignore) setError("Could not load deletion requests");
      } finally {
        if (!ignore) setLoaded(true);
      }
    })();
    return () => {
      ignore = true;
    };
  }, []);

  async function handleReview(id: number, action: "approve" | "reject") {
    const notes = window.prompt(
      action === "approve" ? "Approval notes (optional):" : "Reason for rejecting:"
    );
    if (notes === null) return; // Cancel

    const res = await apiFetch(`/deletion-requests/${id}/${action}`, {
      method: "POST",
      body: JSON.stringify({ resolution_notes: notes || null }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      alert(typeof data.detail === "string" ? data.detail : "Something went wrong");
      return;
    }
    void reload();
  }

  if (!loaded && !error) return <p className={`${page} text-muted`}>Loading…</p>;
  if (error) return <p className={`${page} text-overdue-on`}>{error}</p>;

  const pending = requests.filter((r) => r.status === "pending");
  const resolved = requests.filter((r) => r.status !== "pending");

  return (
    <div className={`${page} flex flex-col gap-5`}>
      <h1 className={h1}>Deletion requests</h1>

      <section className="flex flex-col gap-2">
        <h2 className="text-xs font-semibold uppercase tracking-[0.04em] text-muted">
          Pending ({pending.length})
        </h2>
        <div className={`${card} overflow-hidden`}>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[560px] text-left text-[12.5px]">
              <thead>
                <tr className="border-b border-line text-[10.5px] uppercase tracking-[0.04em] text-faint">
                  <th className="px-5 py-3 font-medium">PO</th>
                  <th className="px-5 py-3 font-medium">Reason</th>
                  <th className="px-5 py-3 font-medium">Requested by</th>
                  <th className="px-5 py-3" />
                </tr>
              </thead>
              <tbody>
                {pending.map((r) => (
                  <tr key={r.id} className="border-t border-line/70">
                    <td className="px-5 py-3 font-mono">
                      {r.po_number}-{r.po_line}
                    </td>
                    <td className="px-5 py-3">{r.reason}</td>
                    <td className="px-5 py-3 text-muted">{r.requested_by.email}</td>
                    <td className="px-5 py-3">
                      <div className="flex gap-3">
                        <button
                          onClick={() => handleReview(r.id, "approve")}
                          className="text-xs font-medium text-ontrack-on hover:underline"
                        >
                          Approve
                        </button>
                        <button
                          onClick={() => handleReview(r.id, "reject")}
                          className="text-xs font-medium text-overdue-on hover:underline"
                        >
                          Reject
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
                {pending.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-5 py-6 text-center text-faint">
                      Nothing pending.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="flex flex-col gap-2">
        <h2 className="text-xs font-semibold uppercase tracking-[0.04em] text-muted">History</h2>
        <div className={`${card} overflow-hidden`}>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-[12.5px]">
              <thead>
                <tr className="border-b border-line text-[10.5px] uppercase tracking-[0.04em] text-faint">
                  <th className="px-5 py-3 font-medium">PO</th>
                  <th className="px-5 py-3 font-medium">Status</th>
                  <th className="px-5 py-3 font-medium">Reason</th>
                  <th className="px-5 py-3 font-medium">Reviewed by</th>
                  <th className="px-5 py-3 font-medium">Notes</th>
                </tr>
              </thead>
              <tbody>
                {resolved.map((r) => (
                  <tr key={r.id} className="border-t border-line/70">
                    <td className="px-5 py-3 font-mono">
                      {r.po_number}-{r.po_line}
                    </td>
                    <td className="px-5 py-3">
                      <span
                        className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          r.status === "approved"
                            ? "bg-overdue-tint text-overdue-on"
                            : "bg-done-tint text-done-on"
                        }`}
                      >
                        {r.status}
                      </span>
                    </td>
                    <td className="px-5 py-3">{r.reason}</td>
                    <td className="px-5 py-3 text-muted">{r.reviewed_by?.email}</td>
                    <td className="px-5 py-3 text-muted">{r.resolution_notes}</td>
                  </tr>
                ))}
                {resolved.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-5 py-6 text-center text-faint">
                      No history yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </div>
  );
}
