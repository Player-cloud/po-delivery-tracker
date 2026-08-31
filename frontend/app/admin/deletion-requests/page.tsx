"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import RequireAdmin from "@/components/RequireAdmin";

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

  if (!loaded && !error) return <p className="p-8">Loading...</p>;
  if (error) return <p className="p-8 text-red-600">{error}</p>;

  const pending = requests.filter((r) => r.status === "pending");
  const resolved = requests.filter((r) => r.status !== "pending");

  return (
    <div className="p-8">
      <h1 className="mb-6 text-xl font-semibold">Deletion Requests</h1>

      <h2 className="mb-2 text-sm font-semibold text-zinc-600">Pending ({pending.length})</h2>
      <table className="mb-8 w-full border-collapse text-left text-sm">
        <thead>
          <tr className="border-b text-xs uppercase text-zinc-400">
            <th className="py-2 font-medium">PO</th>
            <th className="font-medium">Reason</th>
            <th className="font-medium">Requested By</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {pending.map((r) => (
            <tr key={r.id} className="border-b">
              <td className="py-2">
                {r.po_number}-{r.po_line}
              </td>
              <td>{r.reason}</td>
              <td>{r.requested_by.email}</td>
              <td className="flex gap-3 py-2">
                <button
                  onClick={() => handleReview(r.id, "approve")}
                  className="text-green-700 hover:underline"
                >
                  Approve
                </button>
                <button
                  onClick={() => handleReview(r.id, "reject")}
                  className="text-red-600 hover:underline"
                >
                  Reject
                </button>
              </td>
            </tr>
          ))}
          {pending.length === 0 && (
            <tr>
              <td colSpan={4} className="py-4 text-zinc-400">
                Nothing pending.
              </td>
            </tr>
          )}
        </tbody>
      </table>

      <h2 className="mb-2 text-sm font-semibold text-zinc-600">History</h2>
      <table className="w-full border-collapse text-left text-sm">
        <thead>
          <tr className="border-b text-xs uppercase text-zinc-400">
            <th className="py-2 font-medium">PO</th>
            <th className="font-medium">Status</th>
            <th className="font-medium">Reason</th>
            <th className="font-medium">Reviewed By</th>
            <th className="font-medium">Notes</th>
          </tr>
        </thead>
        <tbody>
          {resolved.map((r) => (
            <tr key={r.id} className="border-b">
              <td className="py-2">
                {r.po_number}-{r.po_line}
              </td>
              <td className={r.status === "approved" ? "text-red-600" : "text-zinc-600"}>
                {r.status}
              </td>
              <td>{r.reason}</td>
              <td>{r.reviewed_by?.email}</td>
              <td>{r.resolution_notes}</td>
            </tr>
          ))}
          {resolved.length === 0 && (
            <tr>
              <td colSpan={5} className="py-4 text-zinc-400">
                No history yet.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
