# PO Delivery Tracker — User Guide

A short, practical guide for the team using the tracker day to day. If you
just want to get going, read **Getting started** and **The three screens
you'll use most**; the rest is reference.

---

## What this tool is for

It replaces the delivery spreadsheet. Every **PO line** (not each PO — each
line, because two items on one purchase order often arrive on different
days) is tracked on its own. The system works out how many days are left,
what the status is, and emails the assigned person before a line is late.

You never have to "refresh" anything or run a daily update. Open it when
you want to know where things stand.

---

## Getting started

1. **Sign in** at the app URL your administrator gave you, using the email
   and temporary password they set. Change the password with **Reset
   password** on your own account if you want something memorable
   (10+ characters).
2. You'll land on the **Dashboard**. In the top-left you'll see a
   **Getting started** checklist — it disappears once you've worked
   through it or you click **Dismiss**.
3. Click **Take the 2-minute tour** in that checklist for a guided
   walk-through of each screen. You can re-open it any time from the same
   place until you finish it.

---

## The bar at the top (the "Today" strip)

The dark strip under the menu is always there, on every screen:

- **overdue** — lines past their promised date, not yet delivered
- **due today** — promised for today
- **this week** — promised within the next 7 days
- **reminders daily 07:00 UTC** — when the reminder emails go out
- Press **`/`** anywhere to jump straight to the PO Lines search box.

It's a glance-and-go summary. The numbers update as you move around.

---

## The three screens you'll use most

### 1. Dashboard

Your starting point.

- **Greeting + date** at the top.
- **KPI cards** — Due today, Overdue, Total open, High priority. The
  numbers count up when the page loads.
- **Urgency bar** — the whole open workload as one coloured bar, with a
  legend and counts.
- **Needs attention** — a short table of the lines closest to trouble.
  Click **Edit** on any row to open it. **View all →** goes to the full
  list.

### 2. PO Lines

The full list, with search and filters.

- **Search** by PO number (top-left box, or press `/` from anywhere).
- **Filter** by status: Upcoming, Due Today, Overdue, Delivered.
- **Clear** resets both.
- Each row has **Edit** and **Request deletion**.
- **+ New PO Line** (top-right of the menu, on every screen) adds one.

### 3. New / Edit PO Line

- **New** needs: PO Number, PO Line number, Issue date, Promised delivery,
  and an assignee.
- **Edit** lets you change the promised date, assignee, priority, notes,
  and tick **Mark as delivered** when it arrives.
- **Attachments** (on the Edit screen) — upload packing slips, emails,
  photos. Click a filename to download it; **Delete** removes one.

---

## Statuses and colours

| Colour | Status | Meaning |
|---|---|---|
| Red | Overdue | Past the promised date, not delivered |
| Orange | Due today | Promised for today |
| Amber | Due soon | Within the next few days |
| Green | On track | Comfortably ahead |
| Grey | Delivered | Marked as arrived — done |

The same colours are used on the badges, the Today strip dots, and the
urgency bar, so they mean the same thing everywhere.

---

## Deleting a line

Nothing is deleted outright. On **PO Lines**, click **Request deletion**,
give a reason, and submit. An administrator sees it under **Deletion
Requests** and either approves (the line is removed) or rejects it (it
stays, with the reason recorded). This keeps a clean audit trail.

---

## Reminder emails

- Sent once a day at **07:00 UTC**.
- The **assigned person** gets them — for lines coming due (on the
  thresholds an administrator sets) and for anything overdue, daily until
  it's delivered.
- If a link in an email doesn't open the right line, sign in first, then
  click it again.

---

## What each role can do

| Role | Can do | Sees |
|---|---|---|
| Administrator | Everything, plus manage users, roles, and reminder thresholds | All lines |
| Manager | Create, edit, request deletion | All lines |
| Staff | Create, edit, request deletion | **Only lines assigned to them** |
| Viewer | Read-only | All lines |

---

## For administrators

Three extra menu items appear for you:

- **Alert Thresholds** — the days-before-due when reminders fire (e.g. 7,
  3, 1). Add or remove values and **Save**. Overdue lines are always
  reminded daily regardless.
- **Users** — add a person (email, temporary password, role), change a
  role, deactivate someone, or reset a password. You can't change your
  own role or deactivate yourself.
- **Deletion Requests** — the pending queue and the full history. Approve
  or reject with a note.

New starters: add them in **Users**, then assign lines to them on the
Edit screen. Once more than one person is assignable, the "Add your team"
step on everyone's Getting started checklist ticks itself off.

---

## Tips

- **Keyboard:** `/` focuses search from anywhere. `Tab` moves through
  every control; the focused one gets a teal outline. In the tour,
  arrow keys move between steps and `Esc` closes it.
- **Reduced motion:** if your system is set to reduce motion, all the
  animations are switched off automatically.
- **Mobile:** the layout adapts — tables scroll sideways, the menu
  collapses labels to icons.
- **Something looks wrong?** Tell your administrator; they have the
  deployment runbook and the incident contact.
