"use client";

import { useEffect, useRef, useState } from "react";
import { apiFetch } from "@/lib/api";

type Attachment = {
  id: number;
  file_name: string;
  content_type: string | null;
  size_bytes: number | null;
  uploaded_at: string;
};

function humanSize(bytes: number | null): string {
  if (bytes == null) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function AttachmentsPanel({ poLineId }: { poLineId: string }) {
  const [items, setItems] = useState<Attachment[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const base = `/po-lines/${poLineId}/attachments`;

  // Used by the upload/delete handlers to refresh after a mutation.
  async function reload() {
    try {
      const r = await apiFetch(base);
      if (r.ok) setItems(await r.json());
    } catch {
      setError("Could not load attachments");
    }
  }

  useEffect(() => {
    let ignore = false;
    (async () => {
      try {
        const r = await apiFetch(base);
        if (!r.ok) throw new Error();
        const data = await r.json();
        if (!ignore) setItems(data);
      } catch {
        if (!ignore) setError("Could not load attachments");
      } finally {
        if (!ignore) setLoading(false);
      }
    })();
    return () => {
      ignore = true;
    };
  }, [base]);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setBusy(true);
    setError("");
    const body = new FormData();
    body.append("file", file);
    const res = await apiFetch(base, { method: "POST", body });
    setBusy(false);
    if (fileRef.current) fileRef.current.value = "";
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      setError(typeof data.detail === "string" ? data.detail : "Upload failed");
      return;
    }
    void reload();
  }

  async function handleDownload(a: Attachment) {
    const res = await apiFetch(`${base}/${a.id}`);
    if (!res.ok) {
      setError("Download failed");
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = a.file_name;
    link.click();
    URL.revokeObjectURL(url);
  }

  async function handleDelete(a: Attachment) {
    if (!confirm(`Delete "${a.file_name}"?`)) return;
    setBusy(true);
    const res = await apiFetch(`${base}/${a.id}`, { method: "DELETE" });
    setBusy(false);
    if (!res.ok) {
      setError("Delete failed");
      return;
    }
    setItems((prev) => prev.filter((x) => x.id !== a.id));
  }

  return (
    <div className="rounded border bg-white p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-medium text-zinc-600">Attachments</h2>
        <label className="cursor-pointer text-sm text-blue-600 hover:underline">
          {busy ? "Working..." : "Upload file"}
          <input
            ref={fileRef}
            type="file"
            onChange={handleUpload}
            disabled={busy}
            className="hidden"
          />
        </label>
      </div>

      {error && <p className="mb-2 text-sm text-red-600">{error}</p>}

      {loading ? (
        <p className="text-sm text-zinc-400">Loading...</p>
      ) : items.length === 0 ? (
        <p className="text-sm text-zinc-400">No files attached.</p>
      ) : (
        <ul className="divide-y text-sm">
          {items.map((a) => (
            <li key={a.id} className="flex items-center justify-between py-2">
              <div className="min-w-0">
                <button
                  onClick={() => handleDownload(a)}
                  className="truncate text-left text-blue-600 hover:underline"
                >
                  {a.file_name}
                </button>
                <span className="ml-2 text-xs text-zinc-400">
                  {humanSize(a.size_bytes)} · {a.uploaded_at.slice(0, 10)}
                </span>
              </div>
              <button
                onClick={() => handleDelete(a)}
                disabled={busy}
                className="ml-4 shrink-0 text-xs text-red-600 hover:underline disabled:opacity-50"
              >
                Delete
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
