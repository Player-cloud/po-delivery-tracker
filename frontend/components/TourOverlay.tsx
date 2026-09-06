"use client";

import { useEffect, useState } from "react";
import { card } from "@/lib/ui";

const STEPS: { title: string; body: string }[] = [
  {
    title: "The Today strip",
    body: "The dark bar at the top is always there. It shows how many PO lines are overdue, due today, and due this week, and when reminders run. Press “/” anywhere to jump to search.",
  },
  {
    title: "Dashboard",
    body: "Your landing page: the key counts, a bar showing how open lines split by urgency, and a “Needs attention” list of everything overdue or due within a week — most urgent first.",
  },
  {
    title: "PO Lines",
    body: "Every purchase-order line is tracked on its own, because two items on one order often arrive on different dates. Search by PO number, filter by status, and the coloured pill tells you the urgency at a glance.",
  },
  {
    title: "Reminders",
    body: "The person a line is assigned to gets an email before it’s due, and daily once it’s overdue — no manual chasing. An administrator can change the day-thresholds under Alert Thresholds.",
  },
  {
    title: "Attachments",
    body: "Open any PO line’s Edit screen to attach invoices, delivery notes, or photos — up to 10 MB each. They’re private to people who can see that line.",
  },
];

export default function TourOverlay({ onClose }: { onClose: () => void }) {
  const [i, setI] = useState(0);
  const step = STEPS[i];
  const last = i === STEPS.length - 1;

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowRight" && !last) setI((n) => n + 1);
      if (e.key === "ArrowLeft" && i > 0) setI((n) => n - 1);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [i, last, onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-strip/40 p-4"
      role="dialog"
      aria-modal="true"
      aria-label="Product tour"
      onClick={onClose}
    >
      <div
        className={`${card} animate-rise w-full max-w-md p-6`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-1 flex items-center gap-1.5">
          {STEPS.map((_, n) => (
            <span
              key={n}
              className={`h-1 flex-1 rounded-full ${n <= i ? "bg-accent" : "bg-line"}`}
            />
          ))}
        </div>
        <h2 className="mt-4 font-display text-lg font-semibold">{step.title}</h2>
        <p className="mt-2 text-sm leading-relaxed text-muted">{step.body}</p>

        <div className="mt-6 flex items-center justify-between">
          <button
            onClick={onClose}
            className="text-sm text-faint hover:text-muted"
          >
            Skip
          </button>
          <div className="flex gap-2">
            {i > 0 && (
              <button
                onClick={() => setI((n) => n - 1)}
                className="rounded-[var(--radius-control)] border border-line px-3 py-1.5 text-sm hover:bg-page"
              >
                Back
              </button>
            )}
            <button
              onClick={() => (last ? onClose() : setI((n) => n + 1))}
              className="rounded-[var(--radius-control)] bg-accent px-4 py-1.5 text-sm font-semibold text-accent-on hover:bg-accent-hover"
            >
              {last ? "Done" : "Next"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
