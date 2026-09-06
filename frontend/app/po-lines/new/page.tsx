"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { extractErrorMessage } from "@/lib/errors";
import { Field, control } from "@/components/Field";
import { btnGhost, btnPrimary, card, h1 } from "@/lib/ui";

type FormState = {
  po_number: string;
  po_line: string;
  issue_date: string;
  promised_delivery: string;
  assigned_to_id: string;
  priority: string;
  notes: string;
};

type AssignableUser = { id: number; email: string };

const initialForm: FormState = {
  po_number: "",
  po_line: "",
  issue_date: "",
  promised_delivery: "",
  assigned_to_id: "",
  priority: "",
  notes: "",
};

export default function NewPOLinePage() {
  const [form, setForm] = useState<FormState>(initialForm);
  const [users, setUsers] = useState<AssignableUser[]>([]);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const router = useRouter();

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

  function set(field: keyof FormState, value: string) {
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
        issue_date: form.issue_date,
        promised_delivery: form.promised_delivery,
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
        <div className="grid grid-cols-[1fr_120px] gap-3">
          <Field label="PO Number">
            <input
              value={form.po_number}
              onChange={(e) => set("po_number", e.target.value)}
              className={control}
              required
              autoFocus
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
                {u.email}
              </option>
            ))}
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
