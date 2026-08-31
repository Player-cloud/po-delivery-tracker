// Shared urgency model for the dashboard and the PO Lines list.
// Urgency is a *status* (state), not a category — so every use pairs the colour
// with a text label, never colour alone.

export type UrgencyKey = "overdue" | "today" | "soon" | "later" | "delivered";

type UrgencyStyle = {
  key: UrgencyKey;
  label: string;
  // Tailwind classes for a small pill/badge (subtle fill + readable text + ring).
  badge: string;
  // Solid colour for the composition-bar segment and the legend dot.
  bar: string;
  dot: string;
};

export const URGENCY: Record<UrgencyKey, UrgencyStyle> = {
  overdue: {
    key: "overdue",
    label: "Overdue",
    badge: "bg-red-50 text-red-700 ring-1 ring-inset ring-red-600/20",
    bar: "bg-red-600",
    dot: "bg-red-600",
  },
  today: {
    key: "today",
    label: "Due today",
    badge: "bg-orange-50 text-orange-700 ring-1 ring-inset ring-orange-600/20",
    bar: "bg-orange-500",
    dot: "bg-orange-500",
  },
  soon: {
    key: "soon",
    label: "Due soon",
    badge: "bg-amber-50 text-amber-800 ring-1 ring-inset ring-amber-600/20",
    bar: "bg-amber-400",
    dot: "bg-amber-400",
  },
  later: {
    key: "later",
    label: "On track",
    badge: "bg-green-50 text-green-700 ring-1 ring-inset ring-green-600/20",
    bar: "bg-green-600",
    dot: "bg-green-600",
  },
  delivered: {
    key: "delivered",
    label: "Delivered",
    badge: "bg-zinc-100 text-zinc-600 ring-1 ring-inset ring-zinc-500/20",
    bar: "bg-zinc-400",
    dot: "bg-zinc-400",
  },
};

// Maps a PO line's live state to an urgency bucket. `soon` is 1..7 days out,
// matching the backend's dashboard partition (overdue / today / due_soon / later).
export function urgencyOf(line: {
  delivered: boolean;
  days_remaining: number;
}): UrgencyStyle {
  if (line.delivered) return URGENCY.delivered;
  if (line.days_remaining < 0) return URGENCY.overdue;
  if (line.days_remaining === 0) return URGENCY.today;
  if (line.days_remaining <= 7) return URGENCY.soon;
  return URGENCY.later;
}

// Human phrasing for the "days remaining" column.
export function daysRemainingLabel(days: number): string {
  if (days < 0) return `${Math.abs(days)}d overdue`;
  if (days === 0) return "due today";
  if (days === 1) return "1 day";
  return `${days} days`;
}
