// Shared API shapes (M8). Pages historically declared these inline; new/updated
// screens import from here so the PO / line contract stays in one place.

export type DeliveryStatus = "not_delivered" | "partial" | "complete";
export type PurchaseOrderStatus = "open" | "delivered" | "closed" | "cancelled";
export type Priority = "high" | "medium" | "low";

export type AssignableUser = {
  id: number;
  email: string;
  full_name: string | null;
  display_name: string;
};

export type POLineRef = {
  id: number;
  po_number: string;
  status: PurchaseOrderStatus;
};

export type POLine = {
  id: number;
  purchase_order_id: number;
  po_number: string;
  po_line: number;
  quantity: number;
  issue_date: string;
  promised_delivery: string;
  delivery_status: DeliveryStatus;
  delivered: boolean;
  priority: Priority | null;
  notes: string | null;
  lead_time_days: number | null;
  days_remaining: number;
  status: string;
  assigned_to_id: number | null;
  assigned_to: AssignableUser | null;
  purchase_order: POLineRef | null;
};

export type PurchaseOrder = {
  id: number;
  po_number: string;
  status: PurchaseOrderStatus;
  line_count: number;
  lines_complete: number;
  created_at: string;
  modified_at: string;
};

export type PurchaseOrderDetail = PurchaseOrder & { lines: POLine[] };
