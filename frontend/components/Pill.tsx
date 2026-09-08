import { DELIVERY, PO_STATUS } from "@/lib/status";
import type { DeliveryStatus, PurchaseOrderStatus } from "@/lib/types";

function Pill({ label, badge, dot }: { label: string; badge: string; dot: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${badge}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${dot}`} aria-hidden />
      {label}
    </span>
  );
}

export function DeliveryPill({ status }: { status: DeliveryStatus }) {
  return <Pill {...DELIVERY[status]} />;
}

export function POStatusPill({ status }: { status: PurchaseOrderStatus }) {
  return <Pill {...PO_STATUS[status]} />;
}
