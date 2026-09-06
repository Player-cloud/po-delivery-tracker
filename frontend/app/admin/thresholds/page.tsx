"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import RequireAdmin from "@/components/RequireAdmin";
import { btnGhost, btnPrimary, card, h1, input } from "@/lib/ui";

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

  if (!loaded && !error) return <p className="mx-auto max-w-lg p-6 text-muted">Loading…</p>;

  return (
    <div className="mx-auto max-w-lg px-4 py-6 sm:px-6">
      <h1 className={`${h1} mb-1`}>Alert Thresholds</h1>
      <p className="mb-6 text-sm text-muted">
        Days before a PO line&rsquo;s promised date to send a reminder. Overdue lines
        are reminded daily regardless.
      </p>

      <div className={`${card} p-5`}>
        <div className="mb-4 flex flex-wrap gap-2">
          {days.map((d) => (
            <span
              key={d}
              className="inline-flex items-center gap-2 rounded-full bg-accent-soft px-3 py-1 text-sm text-accent-hover"
            >
              {d} {d === 1 ? "day" : "days"}
              <button
                onClick={() => removeDay(d)}
                className="text-accent hover:text-accent-hover"
                aria-label={`Remove ${d} day threshold`}
              >
                ×
              </button>
            </span>
          ))}
          {days.length === 0 && <span className="text-sm text-faint">No thresholds.</span>}
        </div>

        <form onSubmit={addDay} className="mb-5 flex gap-2">
          <input
            type="number"
            min={0}
            placeholder="Add days"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            className={`${input} w-32`}
            aria-label="Days before due to add"
          />
          <button type="submit" className={btnGhost}>
            Add
          </button>
        </form>

        {error && <p className="mb-3 text-sm text-overdue-on">{error}</p>}
        {saved && <p className="mb-3 text-sm text-ontrack-on">Saved.</p>}

        <button onClick={save} disabled={saving} className={btnPrimary}>
          {saving ? "Saving…" : "Save thresholds"}
        </button>
      </div>
    </div>
  );
}
