"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { apiFetch } from "@/lib/api";
import AttachmentsPanel from "@/components/AttachmentsPanel";
import { Field, control } from "@/components/Field";
import { assigneeLabel } from "@/lib/status";
import { btnGhost, btnPrimary, card, h1 } from "@/lib/ui";
import type { AssignableUser, DeliveryStatus } from "@/lib/types";

type FormState = {
  po_number: string;
  po_line: number;
  description: string;
  promised_delivery: string;
  assigned_to_id: string;
  priority: string;
  notes: string;
  delivery_status: DeliveryStatus;
};

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
            po_number: data.po_number,
            po_line: data.po_line,
            description: data.description || "",
            promised_delivery: data.promised_delivery,
            assigned_to_id: data.assigned_to_id ? String(data.assigned_to_id) : "",
            priority: data.priority || "",
            notes: data.notes || "",
            delivery_status: data.delivery_status,
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
        description: form.description.trim() || null,
        promised_delivery: form.promised_delivery,
        assigned_to_id: Number(form.assigned_to_id),
        priority: form.priority || null,
        notes: form.notes || null,
        delivery_status: form.delivery_status,
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
      <div>
        <h1 className={h1}>Edit PO Line</h1>
        <p className="mt-1 text-sm text-muted">
          PO {form.po_number} · Line {form.po_line}
        </p>
      </div>

      <form onSubmit={handleSubmit} className={`${card} flex flex-col gap-4 p-6`}>
        <Field label="Description" hint="What this line item is.">
          <input
            value={form.description}
            onChange={(e) => updateField("description", e.target.value)}
            className={control}
            placeholder="e.g. 10x M6 bolts, zinc"
            maxLength={500}
          />
        </Field>

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
                {assigneeLabel(u)}
              </option>
            ))}
          </select>
        </Field>

        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Delivery status">
            <select
              value={form.delivery_status}
              onChange={(e) => updateField("delivery_status", e.target.value as DeliveryStatus)}
              className={control}
            >
              <option value="not_delivered">Not delivered</option>
              <option value="partial">Partial</option>
              <option value="complete">Complete</option>
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
        </div>

        <Field label="Notes">
          <textarea
            value={form.notes}
            onChange={(e) => updateField("notes", e.target.value)}
            className={control}
            rows={3}
          />
        </Field>

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
