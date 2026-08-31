"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import RequireAdmin from "@/components/RequireAdmin";

export default function ThresholdsPage() {
  return (
    <RequireAdmin>
      <Thresholds />
    </RequireAdmin>
  );
}

function Thresholds() {
  const [days, setDays] = useState<number[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let ignore = false;
    (async () => {
      try {
        const res = await apiFetch("/config/thresholds");
        if (!res.ok) throw new Error();
        const data = await res.json();
        if (!ignore) setDays(data.thresholds_days);
      } catch {
        if (!ignore) setError("Could not load thresholds");
      } finally {
        if (!ignore) setLoaded(true);
      }
    })();
    return () => {
      ignore = true;
    };
  }, []);

  function addDay(e: React.FormEvent) {
    e.preventDefault();
    const n = Number(draft);
    if (!Number.isInteger(n) || n < 0) {
      setError("Enter a whole number of days (0 or more).");
      return;
    }
    setError("");
    setSaved(false);
    setDays((prev) => Array.from(new Set([...prev, n])).sort((a, b) => b - a));
    setDraft("");
  }

  function removeDay(n: number) {
    setSaved(false);
    setDays((prev) => prev.filter((d) => d !== n));
  }

  async function save() {
    if (days.length === 0) {
      setError("Keep at least one threshold.");
      return;
    }
    setSaving(true);
    setError("");
    const res = await apiFetch("/config/thresholds", {
      method: "PUT",
      body: JSON.stringify({ thresholds_days: days }),
    });
    setSaving(false);
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      setError(typeof data.detail === "string" ? data.detail : "Save failed");
      return;
    }
    const data = await res.json();
    setDays(data.thresholds_days);
    setSaved(true);
  }

  if (!loaded && !error) return <p className="p-8">Loading...</p>;

  return (
    <div className="mx-auto max-w-lg p-8">
      <h1 className="mb-2 text-xl font-semibold">Alert Thresholds</h1>
      <p className="mb-6 text-sm text-zinc-600">
        Days before a PO line&rsquo;s promised date to send a reminder. Overdue lines
        are reminded daily regardless.
      </p>

      <div className="mb-4 flex flex-wrap gap-2">
        {days.map((d) => (
          <span
            key={d}
            className="inline-flex items-center gap-2 rounded-full bg-blue-50 px-3 py-1 text-sm text-blue-800 ring-1 ring-inset ring-blue-600/20"
          >
            {d} {d === 1 ? "day" : "days"}
            <button
              onClick={() => removeDay(d)}
              className="text-blue-500 hover:text-blue-900"
              aria-label={`Remove ${d}`}
            >
              ×
            </button>
          </span>
        ))}
        {days.length === 0 && <span className="text-sm text-zinc-400">No thresholds.</span>}
      </div>

      <form onSubmit={addDay} className="mb-6 flex gap-2">
        <input
          type="number"
          min={0}
          placeholder="Add days"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          className="w-32 rounded border px-3 py-2 text-sm"
        />
        <button type="submit" className="rounded border px-3 py-2 text-sm hover:bg-zinc-50">
          Add
        </button>
      </form>

      {error && <p className="mb-3 text-sm text-red-600">{error}</p>}
      {saved && <p className="mb-3 text-sm text-green-700">Saved.</p>}

      <button
        onClick={save}
        disabled={saving}
        className="rounded bg-black px-4 py-2 text-white hover:bg-zinc-800 disabled:opacity-50"
      >
        {saving ? "Saving..." : "Save thresholds"}
      </button>
    </div>
  );
}
