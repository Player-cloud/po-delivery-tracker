"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";

type FormState = {
  po_number: string;
  po_line: string;
  issue_date: string;
  promised_delivery: string;
  priority: string;
  notes: string;
};

const initialForm: FormState = {
  po_number: "",
  po_line: "",
  issue_date: "",
  promised_delivery: "",
  priority: "",
  notes: "",
};

export default function NewPOLinePage() {
  const [form, setForm] = useState<FormState>(initialForm);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const router = useRouter();

  function updateField(field: keyof FormState, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);

    const response = await apiFetch("/po-lines", {
      method: "POST",
      body: JSON.stringify({
        po_number: form.po_number,
        po_line: Number(form.po_line),
        issue_date: form.issue_date,
        promised_delivery: form.promised_delivery,
        priority: form.priority || null,
        notes: form.notes || null,
      }),
    });

    setSubmitting(false);

    if (!response.ok) {
      const data = await response.json();
      setError(extractErrorMessage(data));
      return;
    }

    router.push("/po-lines");
  }

  return (
    <div className="mx-auto max-w-lg p-8">
      <h1 className="mb-4 text-xl font-semibold">New PO Line</h1>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <input
          placeholder="PO Number"
          value={form.po_number}
          onChange={(e) => updateField("po_number", e.target.value)}
          className="rounded border px-3 py-2"
          required
        />

        <input
          type="number"
          placeholder="PO Line"
          value={form.po_line}
          onChange={(e) => updateField("po_line", e.target.value)}
          className="rounded border px-3 py-2"
          required
        />

        <label className="text-sm text-zinc-600">
          Issue Date
          <input
            type="date"
            value={form.issue_date}
            onChange={(e) => updateField("issue_date", e.target.value)}
            className="mt-1 w-full rounded border px-3 py-2"
            required
          />
        </label>

        <label className="text-sm text-zinc-600">
          Promised Delivery
          <input
            type="date"
            value={form.promised_delivery}
            onChange={(e) => updateField("promised_delivery", e.target.value)}
            className="mt-1 w-full rounded border px-3 py-2"
            required
          />
        </label>

        <select
          value={form.priority}
          onChange={(e) => updateField("priority", e.target.value)}
          className="rounded border px-3 py-2"
        >
          <option value="">Priority (none)</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>

        <textarea
          placeholder="Notes"
          value={form.notes}
          onChange={(e) => updateField("notes", e.target.value)}
          className="rounded border px-3 py-2"
        />

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="rounded bg-black px-4 py-2 text-white hover:bg-zinc-800 disabled:opacity-50"
        >
          {submitting ? "Saving..." : "Create PO Line"}
        </button>
      </form>
    </div>
  );
}

// FastAPI returns two different error shapes depending on what went wrong:
// - Pydantic validation failures (422): { detail: [{ msg, loc, type }, ...] }
// - Your own HTTPException calls, e.g. the duplicate check (409/403/404):
//   { detail: "some string" }
function extractErrorMessage(data: unknown): string {
  if (typeof data === "object" && data !== null && "detail" in data) {
    const detail = (data as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail.map((d: { msg?: string }) => d.msg).join(", ");
    }
  }
  return "Something went wrong";
}