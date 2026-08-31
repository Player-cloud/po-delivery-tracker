"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";

type FormState = {
  promised_delivery: string;
  priority: string;
  notes: string;
  delivered: boolean;
};

export default function EditPOLinePage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const [form, setForm] = useState<FormState | null>(null);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    apiFetch(`/po-lines/${id}`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load PO line");
        return res.json();
      })
      .then((data) =>
        setForm({
          promised_delivery: data.promised_delivery,
          priority: data.priority || "",
          notes: data.notes || "",
          delivered: data.delivered,
        })
      )
      .catch(() => setError("Could not load this PO line"));
  }, [id]);

  function updateField<K extends keyof FormState>(field: K, value: FormState[K]) {
    setForm((prev) => (prev ? { ...prev, [field]: value } : prev));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form) return;
    setError("");
    setSubmitting(true);

    const response = await apiFetch(`/po-lines/${id}`, {
      method: "PUT",
      body: JSON.stringify({
        promised_delivery: form.promised_delivery,
        priority: form.priority || null,
        notes: form.notes || null,
        delivered: form.delivered,
      }),
    });

    setSubmitting(false);

    if (!response.ok) {
      setError("Could not save changes");
      return;
    }

    router.push("/po-lines");
  }

  if (error) return <p className="p-8 text-red-600">{error}</p>;
  if (!form) return <p className="p-8">Loading...</p>;

  return (
    <div className="mx-auto max-w-lg p-8">
      <h1 className="mb-4 text-xl font-semibold">Edit PO Line</h1>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
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

        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={form.delivered}
            onChange={(e) => updateField("delivered", e.target.checked)}
          />
          Delivered
        </label>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="rounded bg-black px-4 py-2 text-white hover:bg-zinc-800 disabled:opacity-50"
        >
          {submitting ? "Saving..." : "Save Changes"}
        </button>
      </form>
    </div>
  );
}