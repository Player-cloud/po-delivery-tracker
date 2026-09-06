"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { apiFetch } from "@/lib/api";
import AttachmentsPanel from "@/components/AttachmentsPanel";
import { Field, control } from "@/components/Field";
import { btnGhost, btnPrimary, card, h1 } from "@/lib/ui";

type FormState = {
  promised_delivery: string;
  assigned_to_id: string;
  priority: string;
  notes: string;
  delivered: boolean;
};

type AssignableUser = { id: number; email: string };

export default function EditPOLinePage() {
  return (
    <Suspense fallback={<p className="mx-auto max-w-lg p-6 text-muted">Loading…</p>}>
      <EditPOLine />
    </Suspense>
  );
}

function EditPOLine() {
  const id = useSearchParams().get("id");
  const router = useRouter();

  const [form, setForm] = useState<FormState | null>(null);
  const [users, setUsers] = useState<AssignableUser[]>([]);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let ignore = false;
    (async () => {
      try {
        const res = await apiFetch("/users/assignable");
        const data = res.ok ? await res.json() : [];
        if (!ignore) setUsers(data);
      } catch {
        if (!ignore) setUsers([]);
      }
    })();
    return () => {
      ignore = true;
    };
  }, []);

  useEffect(() => {
    if (!id) return;
    let ignore = false;
    (async () => {
      try {
        const res = await apiFetch(`/po-lines/${id}`);
        if (!res.ok) throw new Error();
        const data = await res.json();
        if (!ignore) {
          setForm({
            promised_delivery: data.promised_delivery,
            assigned_to_id: data.assigned_to_id ? String(data.assigned_to_id) : "",
            priority: data.priority || "",
            notes: data.notes || "",
            delivered: data.delivered,
          });
        }
      } catch {
        if (!ignore) setError("Could not load this PO line");
      }
    })();
    return () => {
      ignore = true;
    };
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
        assigned_to_id: Number(form.assigned_to_id),
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

  if (!id) return <p className="mx-auto max-w-lg p-6 text-overdue-on">No PO line specified.</p>;
  if (error) return <p className="mx-auto max-w-lg p-6 text-overdue-on">{error}</p>;
  if (!form) return <p className="mx-auto max-w-lg p-6 text-muted">Loading…</p>;

  return (
    <div className="mx-auto flex max-w-lg flex-col gap-6 px-4 py-6 sm:px-6">
      <h1 className={h1}>Edit PO Line</h1>

      <form onSubmit={handleSubmit} className={`${card} flex flex-col gap-4 p-6`}>
        <Field label="Promised delivery">
          <input
            type="date"
            value={form.promised_delivery}
            onChange={(e) => updateField("promised_delivery", e.target.value)}
            className={control}
            required
          />
        </Field>

        <Field label="Assigned to" hint="Reminders go to this person.">
          <select
            value={form.assigned_to_id}
            onChange={(e) => updateField("assigned_to_id", e.target.value)}
            className={control}
            required
          >
            <option value="" disabled>
              Select an assignee
            </option>
            {users.map((u) => (
              <option key={u.id} value={String(u.id)}>
                {u.email}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Priority">
          <select
            value={form.priority}
            onChange={(e) => updateField("priority", e.target.value)}
            className={control}
          >
            <option value="">None</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </Field>

        <Field label="Notes">
          <textarea
            value={form.notes}
            onChange={(e) => updateField("notes", e.target.value)}
            className={control}
            rows={3}
          />
        </Field>

        <label className="flex items-center gap-2.5 text-sm">
          <input
            type="checkbox"
            checked={form.delivered}
            onChange={(e) => updateField("delivered", e.target.checked)}
            className="h-4 w-4 accent-accent"
          />
          Mark as delivered
        </label>

        {error && <p className="text-sm text-overdue-on">{error}</p>}

        <div className="flex gap-2">
          <button type="submit" disabled={submitting} className={btnPrimary}>
            {submitting ? "Saving…" : "Save changes"}
          </button>
          <Link href="/po-lines" className={btnGhost}>
            Cancel
          </Link>
        </div>
      </form>

      <AttachmentsPanel poLineId={id} />
    </div>
  );
}
