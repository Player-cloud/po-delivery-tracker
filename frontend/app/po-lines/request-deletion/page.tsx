"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { apiFetch } from "@/lib/api";

type POLine = {
  po_number: string;
  po_line: number;
};

export default function RequestDeletionPage() {
  return (
    <Suspense fallback={<p className="p-8">Loading...</p>}>
      <RequestDeletion />
    </Suspense>
  );
}

function RequestDeletion() {
  const id = useSearchParams().get("id");
  const router = useRouter();

  const [poLine, setPOLine] = useState<POLine | null>(null);
  const [reason, setReason] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!id) return;
    let ignore = false;
    (async () => {
      try {
        const res = await apiFetch(`/po-lines/${id}`);
        if (!res.ok) throw new Error();
        const data = await res.json();
        if (!ignore) setPOLine(data);
      } catch {
        if (!ignore) setError("Could not load this PO line");
      }
    })();
    return () => {
      ignore = true;
    };
  }, [id]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);

    const response = await apiFetch(`/po-lines/${id}/deletion-requests`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    });

    setSubmitting(false);

    if (!response.ok) {
      const data = await response.json();
      setError(typeof data.detail === "string" ? data.detail : "Something went wrong");
      return;
    }

    router.push("/po-lines");
  }

  if (!id) return <p className="p-8 text-red-600">No PO line specified.</p>;
  if (error && !poLine) return <p className="p-8 text-red-600">{error}</p>;
  if (!poLine) return <p className="p-8">Loading...</p>;

  return (
    <div className="mx-auto max-w-lg p-8">
      <h1 className="mb-2 text-xl font-semibold">Request Deletion</h1>
      <p className="mb-4 text-sm text-zinc-600">
        PO {poLine.po_number}, Line {poLine.po_line}
      </p>

      <div className="mb-4 rounded border border-yellow-300 bg-yellow-50 p-3 text-sm text-yellow-800">
        This won&apos;t delete the item immediately — it sends a request to an
        Administrator, who can approve or reject it.
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <label className="text-sm text-zinc-600">
          Reason
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="mt-1 w-full rounded border px-3 py-2"
            rows={4}
            required
            placeholder="Why should this be deleted?"
          />
        </label>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={submitting}
            className="rounded bg-red-600 px-4 py-2 text-white hover:bg-red-700 disabled:opacity-50"
          >
            {submitting ? "Submitting..." : "Submit Request"}
          </button>
          <button
            type="button"
            onClick={() => router.push("/po-lines")}
            className="rounded border px-4 py-2 hover:bg-zinc-50"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
