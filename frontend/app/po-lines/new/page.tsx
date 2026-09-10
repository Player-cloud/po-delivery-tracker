"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { extractErrorMessage } from "@/lib/errors";
import { assigneeLabel } from "@/lib/status";
import { Field, control } from "@/components/Field";
import { btnGhost, btnPrimary, card, h1 } from "@/lib/ui";
import type { AssignableUser, DeliveryStatus } from "@/lib/types";

type FormState = {
  po_number: string;
  po_line: string;
  description: string;
  issue_date: string;
  promised_delivery: string;
  delivery_status: DeliveryStatus;
  assigned_to_id: string;
  priority: string;
  notes: string;
};

const initialForm: FormState = {
  po_number: "",
  po_line: "",
  description: "",
  issue_date: "",
  promised_delivery: "",
  delivery_status: "not_delivered",
  assigned_to_id: "",
  priority: "",
  notes: "",
};

export default function NewPOLinePage() {
  return (
    <Suspense fallback={<p className="mx-auto max-w-lg p-6 text-muted">Loading…</p>}>
      <NewPOLine />
    </Suspense>
  );
}

function NewPOLine() {
  const router = useRouter();
  const poParam = useSearchParams().get("po");

  const [form, setForm] = useState<FormState>(() =>
    poParam ? { ...initialForm, po_number: poParam } : initialForm,
  );
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

  function set<K extends keyof FormState>(field: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    const res = await apiFetch("/po-lines", {
      method: "POST",
      body: JSON.stringify({
        po_number: form.po_number,
        po_line: Number(form.po_line),
        description: form.description.trim() || null,
        issue_date: form.issue_date,
        promised_delivery: form.promised_delivery,
        delivery_status: form.delivery_status,
        assigned_to_id: Number(form.assigned_to_id),
        priority: form.priority || null,
        notes: form.notes || null,
      }),
    });
    setSubmitting(false);
    if (!res.ok) {
      setError(extractErrorMessage(await res.json().catch(() => ({}))));
      return;
    }
    router.push("/po-lines");
  }

  return (
    <div className="mx-auto max-w-lg px-4 py-6 sm:px-6">
      <h1 className={`${h1} mb-4`}>New PO Line</h1>

      <form onSubmit={handleSubmit} className={`${card} flex flex-col gap-4 p-6`}>
        <div className="grid grid-cols-[1fr_100px] gap-3">
          <Field label="PO Number">
            <input
              value={form.po_number}
              onChange={(e) => set("po_number", e.target.value)}
              className={control}
              required
              autoFocus={!poParam}
            />
          </Field>
          <Field label="Line">
            <input
              type="number"
              min={1}
              value={form.po_line}
              onChange={(e) => set("po_line", e.target.value)}
              className={control}
              required
            />
          </Field>
        </div>

        <Field label="Description" hint="What this line item is.">
          <input
            value={form.description}
            onChange={(e) => set("description", e.target.value)}
            className={control}
            placeholder="e.g. 10x M6 bolts, zinc"
            maxLength={500}
          />
        </Field>

        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Issue date">
            <input
              type="date"
              value={form.issue_date}
              onChange={(e) => set("issue_date", e.target.value)}
              className={control}
              required
            />
          </Field>
          <Field label="Promised delivery">
            <input
              type="date"
              value={form.promised_delivery}
              onChange={(e) => set("promised_delivery", e.target.value)}
              className={control}
              required
            />
          </Field>
        </div>

        <Field label="Assigned to" hint="Reminders go to this person.">
          <select
            value={form.assigned_to_id}
            onChange={(e) => set("assigned_to_id", e.target.value)}
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
              onChange={(e) => set("delivery_status", e.target.value as DeliveryStatus)}
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
              onChange={(e) => set("priority", e.target.value)}
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
            onChange={(e) => set("notes", e.target.value)}
            className={control}
            rows={3}
          />
        </Field>

        {error && <p className="text-sm text-overdue-on">{error}</p>}

        <div className="flex gap-2">
          <button type="submit" disabled={submitting} className={btnPrimary}>
            {submitting ? "Saving…" : "Create PO Line"}
          </button>
          <Link href="/po-lines" className={btnGhost}>
            Cancel
          </Link>
        </div>
      </form>
    </div>
  );
}
