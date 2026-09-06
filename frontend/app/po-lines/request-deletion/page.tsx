"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { extractErrorMessage } from "@/lib/errors";
import { Field, control } from "@/components/Field";
import { btnGhost, card, h1 } from "@/lib/ui";

type POLine = {
  po_number: string;
  po_line: number;
};

export default function RequestDeletionPage() {
  return (
    <Suspense fallback={<p className="mx-auto max-w-lg p-6 text-muted">Loading…</p>}>
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
      setError(extractErrorMessage(await response.json().catch(() => ({}))));
      return;
    }

    router.push("/po-lines");
  }

  if (!id) return <p className="mx-auto max-w-lg p-6 text-overdue-on">No PO line specified.</p>;
  if (error && !poLine) return <p className="mx-auto max-w-lg p-6 text-overdue-on">{error}</p>;
  if (!poLine) return <p className="mx-auto max-w-lg p-6 text-muted">Loading…</p>;

  return (
    <div className="mx-auto max-w-lg px-4 py-6 sm:px-6">
      <h1 className={`${h1} mb-1`}>Request deletion</h1>
      <p className="mb-4 text-sm text-muted">
        PO {poLine.po_number}, Line {poLine.po_line}
      </p>

      <form onSubmit={handleSubmit} className={`${card} flex flex-col gap-4 p-6`}>
        <div className="rounded-[var(--radius-control)] border border-today/40 bg-today-tint p-3 text-sm text-today-on">
          This won&apos;t delete the line — it sends a request to an administrator,
          who approves or rejects it.
        </div>

        <Field label="Reason" hint="Required.">
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className={control}
            rows={4}
            required
            placeholder="Why should this be deleted?"
          />
        </Field>

        {error && <p className="text-sm text-overdue-on">{error}</p>}

        <div className="flex gap-2">
          <button
            type="submit"
            disabled={submitting}
            className="inline-flex items-center justify-center rounded-[var(--radius-control)] bg-overdue px-4 py-2 text-sm font-semibold text-white transition-colors hover:brightness-95 disabled:opacity-50"
          >
            {submitting ? "Submitting…" : "Submit request"}
          </button>
          <button type="button" onClick={() => router.push("/po-lines")} className={btnGhost}>
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
