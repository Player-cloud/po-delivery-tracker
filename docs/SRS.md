# Software Requirements Specification (SRS)
## PO Delivery Tracking System

**Version:** 0.1 (Draft)
**Status:** For review
**Related documents:** `PO_Delivery_Tracking_System_Design.docx` (original SharePoint-based proposal — superseded as the target platform, but still the source of business requirements)

---

## 1. Purpose

This document defines what the PO Delivery Tracking System must do, independent of the platform it runs on. It replaces the SharePoint/Power Platform design with a custom application (FastAPI + PostgreSQL + Next.js), deployed to Azure. The business goals are unchanged from the original proposal: replace the Excel tracker, track PO lines individually, automate delivery reminders, and give managers an at-a-glance dashboard.

## 2. Scope

In scope: PO line delivery tracking, automated reminders, role-based dashboard, reporting, audit trail, file attachments.
Out of scope: inventory management, vendor performance scoring, procurement/ordering workflow (the PO already exists by the time it enters this system).

## 3. Roles

| Role | Description |
|---|---|
| Administrator | Full control: manages users, roles, and alert-threshold configuration |
| Manager | Creates/edits/deletes PO lines, views all dashboards and reports |
| Staff | Views and updates PO lines (all, or assigned-only — TBD with employer), cannot delete |
| Viewer | Read-only access to dashboard and reports |

---

## 4. Functional Requirements

| ID | Requirement |
|---|---|
| FR-1 | The system shall store one record per PO line, keyed uniquely by (PO Number, PO Line) |
| FR-2 | The system shall reject creation of a duplicate (PO Number, PO Line) combination |
| FR-3 | The system shall store: Issue Date, Promised Delivery Date, Delivered flag, Assigned To, Priority, Notes, Attachments |
| FR-4 | The system shall automatically compute Lead Time (days between Issue Date and Promised Delivery) |
| FR-5 | The system shall automatically compute Days Remaining and Status (Upcoming / Due Today / Overdue / Delivered) in real time, without a scheduled refresh job |
| FR-6 | Authorized users shall be able to create, edit, and delete PO lines through a web form |
| FR-7 | The system shall support file attachments per PO line (invoices, receipts, delivery photos) |
| FR-8 | The system shall send automated email reminders at configurable thresholds (default: 30, 14, 7, 3, 1 days before due, due-today, and daily while overdue) |
| FR-9 | Alert thresholds shall be configurable by an Administrator without a code change |
| FR-10 | The system shall stop sending reminders for a PO line once it is marked Delivered |
| FR-11 | The system shall provide a dashboard with summary KPIs: Total Open, Due Today, Due This Week, Overdue, Completed, High Priority |
| FR-12 | The dashboard shall show a filterable, sortable list of open PO lines |
| FR-13 | The system shall visually color-code PO lines by urgency, using the same thresholds as Section 9 of the original design document |
| FR-14 | The system shall enforce role-based access control per Section 3 |
| FR-15 | The system shall record who created/modified each record and when (audit trail) |
| FR-16 | The system shall support connecting Power BI (or an equivalent BI tool) directly to the database for reporting |
| FR-17 | The system shall authenticate users; initial implementation via username/password (JWT), with a path to Microsoft Entra ID SSO later without redesigning the app |

## 5. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-1 | Dashboard views shall load in under 2 seconds with up to 5,000 open PO lines |
| NFR-2 | The production deployment shall target 99% uptime |
| NFR-3 | Secrets (DB passwords, API keys, email credentials) shall never be committed to source control; production secrets are stored in Azure Key Vault |
| NFR-4 | The data model shall be normalized to support future growth (multiple vendors, business units) without a schema redesign |
| NFR-5 | The codebase shall include automated unit and integration tests, run in CI on every push |
| NFR-6 | The full application shall run locally via `docker compose up`, with no dependency on Azure for local development |
| NFR-7 | The UI and API shall both validate input (no past Promised Dates, no duplicate PO+Line) — never rely on UI-only validation |
| NFR-8 | Every write operation shall be attributable to an authenticated user and timestamp |

---

## 6. User Stories & Acceptance Criteria

### US-1 — Create a PO line (Staff/Manager)
*As a staff member, I want to create a new PO line so I can start tracking its delivery.*
- **Given** I am logged in as Staff or Manager, **when** I submit the form with PO Number, PO Line, Issue Date, and Promised Delivery, **then** a new record is created and Lead Time, Days Remaining, and Status are calculated automatically.
- **Given** I submit a PO Number + Line that already exists, **when** I try to save, **then** the system rejects it with a clear duplicate error.
- **Given** I enter a Promised Delivery date in the past, **when** I try to save, **then** the system flags it before submission.

### US-2 — View the dashboard (Manager/Viewer)
*As a manager, I want a dashboard of all open PO lines color-coded by urgency, so I can prioritize which vendors to follow up with today.*
- **Given** I open the dashboard, **when** the page loads, **then** I see KPI counts and a color-coded list matching the current data within 2 seconds.

### US-3 — Receive a reminder (any assigned user)
*As an assigned staff member, I want an email reminder 7 days before a delivery is due, so I don't miss it.*
- **Given** a PO line has 7 days remaining and is not Delivered, **when** the daily check runs, **then** an email is sent to the Assigned To user with PO details and a link to the record.
- **Given** a PO line is marked Delivered, **when** the daily check runs, **then** no further reminders are sent for it.

### US-4 — Configure alert thresholds (Administrator)
*As an administrator, I want to configure the reminder thresholds, so the business can adjust urgency rules without a developer.*
- **Given** I am logged in as Administrator, **when** I update the threshold configuration, **then** the next scheduled run uses the new values without a deployment.

### US-5 — Mark a line as Delivered (Staff/Manager)
*As a staff member, I want to mark a PO line as Delivered, so it stops generating reminders and is reflected in reporting.*
- **Given** I check the Delivered box and save, **when** the record updates, **then** Status changes to "Delivered" and it is excluded from future reminder runs.

### US-6 — Read-only access (Viewer)
*As a read-only viewer, I want to see the dashboard and reports without being able to edit records, so data integrity is protected.*
- **Given** I am logged in as Viewer, **when** I open any PO line, **then** all fields are read-only and no save/delete controls are shown.

### US-7 — Attach a document (Staff/Manager)
*As a staff member, I want to attach a delivery receipt to a PO line, so proof of delivery is stored with the record.*
- **Given** I open a PO line, **when** I upload a file, **then** it is stored and a link to it appears on the record for all authorized users.

### US-8 — Audit a change (Administrator)
*As an administrator, I want to see who changed a record and when, so I can investigate discrepancies.*
- **Given** a PO line has been edited, **when** I view its history, **then** I see each change with the user and timestamp.

---

## 7. Open Questions for Employer / Stakeholder

1. Should Staff see all PO lines or only ones assigned to them?
2. Should overdue reminders really repeat daily indefinitely, or stop after some number of repeats / escalate to a manager?
3. Any existing vendor or business-unit data that should be modeled now rather than retrofitted later?
4. Any branding requirements for the UI or the email templates?
5. Is SSO via Microsoft Entra ID required for launch, or acceptable to add after an initial JWT-based release?

---

## 8. Traceability to Original Design Document

Every functional requirement above maps directly to a section of the original SharePoint-based design document — the *business logic* (thresholds, roles, calculated fields, color-coding) is unchanged; only the *implementation platform* has changed. Where the two documents differ (e.g. FR-5's real-time computed Status vs. the original's daily-flow-refreshed Status), the new approach is a technical improvement enabled by moving off SharePoint's calculated-column limitations, not a change in business intent.
