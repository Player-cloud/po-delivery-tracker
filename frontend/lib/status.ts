// Presentation for the M8 status enums — colour always paired with a label.

import type { AssignableUser, DeliveryStatus, PurchaseOrderStatus } from "@/lib/types";

type Style = { label: string; badge: string; dot: string };

export const DELIVERY: Record<DeliveryStatus, Style> = {
  not_delivered: {
    label: "Not delivered",
    badge: "bg-surface-tint text-muted",
    dot: "bg-faint",
  },
  partial: {
    label: "Partial",
    badge: "bg-soon-tint text-soon-on",
    dot: "bg-soon",
  },
  complete: {
    label: "Complete",
    badge: "bg-done-tint text-done-on",
    dot: "bg-done",
  },
};

export const PO_STATUS: Record<PurchaseOrderStatus, Style> = {
  open: { label: "Open", badge: "bg-accent-soft text-accent-hover", dot: "bg-accent" },
  delivered: { label: "Delivered", badge: "bg-ontrack-tint text-ontrack-on", dot: "bg-ontrack" },
  closed: { label: "Closed", badge: "bg-done-tint text-done-on", dot: "bg-done" },
  cancelled: { label: "Cancelled", badge: "bg-overdue-tint text-overdue-on", dot: "bg-overdue" },
};

/** "Full Name (email)" when we have a name, else the email. */
export function assigneeLabel(user: Pick<AssignableUser, "email" | "full_name"> | null): string {
  if (!user) return "—";
  return user.full_name ? `${user.full_name} (${user.email})` : user.email;
}
