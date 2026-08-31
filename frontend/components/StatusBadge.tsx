import { urgencyOf } from "@/lib/urgency";

// A small pill showing a PO line's live urgency. Colour + label together — the
// label carries the meaning, the colour reinforces it.
export default function StatusBadge({
  delivered,
  days_remaining,
}: {
  delivered: boolean;
  days_remaining: number;
}) {
  const u = urgencyOf({ delivered, days_remaining });
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${u.badge}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${u.dot}`} aria-hidden />
      {u.label}
    </span>
  );
}
