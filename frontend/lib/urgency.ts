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
    badge: "bg-overdue-tint text-overdue-on",
    bar: "bg-overdue",
    dot: "bg-overdue",
  },
  today: {
    key: "today",
    label: "Due today",
    badge: "bg-today-tint text-today-on",
    bar: "bg-today",
    dot: "bg-today",
  },
  soon: {
    key: "soon",
    label: "Due soon",
    badge: "bg-soon-tint text-soon-on",
    bar: "bg-soon",
    dot: "bg-soon",
  },
  later: {
    key: "later",
    label: "On track",
    badge: "bg-ontrack-tint text-ontrack-on",
    bar: "bg-ontrack",
    dot: "bg-ontrack",
  },
  delivered: {
    key: "delivered",
    label: "Delivered",
    badge: "bg-done-tint text-done-on",
    bar: "bg-done",
    dot: "bg-done",
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
