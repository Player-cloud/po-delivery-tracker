"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { getUserRole } from "@/lib/auth";

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
  const [requests, setRequests] = useState<DeletionRequest[]>([]);
  const [error, setError] = useState("");
  const [authorized, setAuthorized] = useState<boolean | null>(null);
  const router = useRouter();

  useEffect(() => {
    if (getUserRole() !== "administrator") {
      setAuthorized(false);
      return;
    }
    setAuthorized(true);
    loadRequests();
  }, []);

  function loadRequests() {
    apiFetch("/deletion-requests")
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load");
        return res.json();
      })
      .then((data) => setRequests(data))
      .catch(() => setError("Could not load deletion requests"));
  }

  async function handleReview(id: number, action: "approve" | "reject") {
    const notes = window.prompt(
      action === "approve" ? "Approval notes (optional):" : "Reason for rejecting:"
    );
    if (notes === null) return; // user hit Cancel on the prompt

    const response = await apiFetch(`/deletion-requests/${id}/${action}`, {
      method: "POST",
      body: JSON.stringify({ resolution_notes: notes || null }),
    });

    if (!response.ok) {
      const data = await response.json();
      alert(typeof data.detail === "string" ? data.detail : "Something went wrong");
      return;
    }

    loadRequests(); // refresh the list to reflect the new status
  }

  if (authorized === false) {
    return <p className="p-8 text-red-600">Administrators only.</p>;
  }
  if (authorized === null) return <p className="p-8">Loading...</p>;
  if (error) return <p className="p-8 text-red-600">{error}</p>;

  const pending = requests.filter((r) => r.status === "pending");
  const resolved = requests.filter((r) => r.status !== "pending");

  return (
    <div className="p-8">
      <h1 className="mb-6 text-xl font-semibold">Deletion Requests</h1>

      <h2 className="mb-2 text-sm font-semibold text-zinc-600">
        Pending ({pending.length})
      </h2>
      <table className="mb-8 w-full border-collapse text-left text-sm">
        <thead>
          <tr className="border-b">
            <th className="py-2">PO</th>
            <th>Reason</th>
            <th>Requested By</th>
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
          <tr className="border-b">
            <th className="py-2">PO</th>
            <th>Status</th>
            <th>Reason</th>
            <th>Reviewed By</th>
            <th>Notes</th>
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
        </tbody>
      </table>
    </div>
  );
}